"""Website preview generation.

Strategy (first one that works wins):
  1. Real screenshot with headless Chromium (Playwright).
  2. Screenshot from the thum.io service (only if USE_THUMIO_FALLBACK=true) -
     useful for sites that block headless browsers / data-centre IPs.
  3. The page's Open Graph image (og:image / twitter:image).
  4. A generated placeholder card, so a submitted URL is always saved with a preview.
"""
import io
import ipaddress
import logging
import re
import socket
import uuid
from typing import Optional, Tuple
from urllib.parse import quote, urljoin, urlparse

import httpx
from bs4 import BeautifulSoup
from PIL import Image, ImageDraw, ImageFont

from . import config

log = logging.getLogger("preview")

VIEWPORT = {"width": 1366, "height": 768}
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
BLOCK_MARKERS = (
    "access denied",
    "forbidden",
    "just a moment",
    "attention required",
    "captcha",
    "are you a robot",
    "request blocked",
)
MAX_IMAGE_BYTES = 8 * 1024 * 1024
OUTPUT_WIDTH = 1000


# --------------------------------------------------------------------------- #
# URL safety
# --------------------------------------------------------------------------- #
def normalize_url(raw: str) -> str:
    raw = raw.strip()
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", raw):
        raw = "https://" + raw
    return raw


def validate_public_url(raw: str) -> str:
    """Return a normalised URL, or raise ValueError if it is not a public http(s) URL."""
    url = normalize_url(raw)
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http and https URLs are supported.")
    host = parsed.hostname
    if not host or "." not in host and host != "localhost":
        raise ValueError("Enter a valid website address, e.g. https://example.com")
    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror:
        raise ValueError(f"Could not resolve '{host}'. Check the address and try again.")
    for info in infos:
        ip = ipaddress.ip_address(info[4][0])
        if not ip.is_global:
            raise ValueError("That address points to a private network and can't be previewed.")
    return url


def _safe_get(url: str, max_redirects: int = 5, **kwargs) -> httpx.Response:
    """GET that re-validates every redirect hop against the public-URL rule."""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,image/*;q=0.8,*/*;q=0.5",
        "Accept-Language": "en-IN,en;q=0.9",
    }
    with httpx.Client(timeout=12, follow_redirects=False, headers=headers) as client:
        current = url
        for _ in range(max_redirects + 1):
            validate_public_url(current)
            resp = client.get(current, **kwargs)
            if resp.is_redirect and resp.headers.get("location"):
                current = urljoin(current, resp.headers["location"])
                continue
            return resp
    raise ValueError("Too many redirects.")


# --------------------------------------------------------------------------- #
# Image helpers
# --------------------------------------------------------------------------- #
def _save_image(img: Image.Image) -> str:
    img = img.convert("RGB")
    if img.width > OUTPUT_WIDTH:
        ratio = OUTPUT_WIDTH / img.width
        img = img.resize((OUTPUT_WIDTH, max(1, int(img.height * ratio))), Image.LANCZOS)
    name = f"{uuid.uuid4().hex}.jpg"
    img.save(config.PREVIEW_DIR / name, "JPEG", quality=82, optimize=True)
    return name


def _image_from_bytes(data: bytes) -> Optional[Image.Image]:
    try:
        img = Image.open(io.BytesIO(data))
        img.load()
        if img.width < 80 or img.height < 80:
            return None
        return img
    except Exception:
        return None


# --------------------------------------------------------------------------- #
# Strategy 1: headless browser
# --------------------------------------------------------------------------- #
def _playwright_screenshot(url: str) -> Tuple[Optional[bytes], Optional[str]]:
    """Return (jpeg_bytes, title). jpeg_bytes is None when failed or blocked."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        log.warning("Playwright is not installed; skipping browser screenshot.")
        return None, None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=True,
                args=["--no-sandbox", "--disable-blink-features=AutomationControlled"],
            )
            try:
                context = browser.new_context(
                    viewport=VIEWPORT,
                    user_agent=USER_AGENT,
                    locale="en-IN",
                    java_script_enabled=True,
                )
                page = context.new_page()
                response = page.goto(url, wait_until="domcontentloaded", timeout=30000)
                try:
                    page.wait_for_load_state("networkidle", timeout=8000)
                except Exception:
                    pass  # busy pages never go idle; screenshot what we have
                page.wait_for_timeout(1200)

                title = (page.title() or "").strip()
                status = response.status if response else 0
                body_text = ""
                try:
                    body_text = (page.inner_text("body", timeout=2000) or "")[:600].lower()
                except Exception:
                    pass

                blocked = status in (401, 403, 429) or status >= 500
                blocked = blocked or any(
                    m in title.lower() or m in body_text[:300] for m in BLOCK_MARKERS
                )
                if blocked:
                    log.info("Browser was blocked by %s (status %s)", url, status)
                    return None, None

                shot = page.screenshot(type="jpeg", quality=85, full_page=False)
                return shot, title or None
            finally:
                browser.close()
    except Exception as exc:  # noqa: BLE001
        log.warning("Playwright screenshot failed for %s: %s", url, exc)
        return None, None


# --------------------------------------------------------------------------- #
# Strategy 2: thum.io
# --------------------------------------------------------------------------- #
def _thumio_screenshot(url: str) -> Optional[bytes]:
    api = f"https://image.thum.io/get/width/1280/crop/800/noanimate/{quote(url, safe=':/?&=%#')}"
    try:
        with httpx.Client(timeout=45, follow_redirects=True) as client:
            resp = client.get(api, headers={"User-Agent": USER_AGENT})
        if resp.status_code == 200 and resp.headers.get("content-type", "").startswith("image/"):
            if len(resp.content) <= MAX_IMAGE_BYTES:
                return resp.content
    except Exception as exc:  # noqa: BLE001
        log.warning("thum.io failed for %s: %s", url, exc)
    return None


# --------------------------------------------------------------------------- #
# Strategy 3: page metadata (title + og:image)
# --------------------------------------------------------------------------- #
def _fetch_metadata(url: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (title, absolute_og_image_url)."""
    try:
        resp = _safe_get(url)
        if resp.status_code >= 400 or "html" not in resp.headers.get("content-type", ""):
            return None, None
        soup = BeautifulSoup(resp.text[:600_000], "html.parser")

        def meta(*names):
            for n in names:
                tag = soup.find("meta", attrs={"property": n}) or soup.find(
                    "meta", attrs={"name": n}
                )
                if tag and tag.get("content"):
                    return tag["content"].strip()
            return None

        title = meta("og:title", "twitter:title") or (
            soup.title.string.strip() if soup.title and soup.title.string else None
        )
        if title and any(m in title.lower() for m in BLOCK_MARKERS):
            title = None
        image = meta("og:image", "og:image:url", "twitter:image")
        if image:
            image = urljoin(str(resp.url), image)
        return title, image
    except Exception as exc:  # noqa: BLE001
        log.info("Metadata fetch failed for %s: %s", url, exc)
        return None, None


def _download_image(image_url: str) -> Optional[bytes]:
    try:
        resp = _safe_get(image_url)
        if resp.status_code == 200 and len(resp.content) <= MAX_IMAGE_BYTES:
            return resp.content
    except Exception as exc:  # noqa: BLE001
        log.info("Image download failed for %s: %s", image_url, exc)
    return None


# --------------------------------------------------------------------------- #
# Strategy 4: generated placeholder
# --------------------------------------------------------------------------- #
def _font(size: int):
    for name in ("DejaVuSans-Bold.ttf", "Arial Bold.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    try:
        return ImageFont.load_default(size=size)
    except TypeError:
        return ImageFont.load_default()


def _placeholder(url: str, title: Optional[str]) -> Image.Image:
    w, h = 1280, 800
    img = Image.new("RGB", (w, h), "#14213D")
    draw = ImageDraw.Draw(img)
    for y in range(h):  # simple vertical gradient
        t = y / h
        r = int(20 + (43 - 20) * t)
        g = int(33 + (89 - 33) * t)
        b = int(61 + (255 - 61) * t)
        draw.line([(0, y), (w, y)], fill=(r, g, b))

    host = urlparse(url).hostname or url
    host = host.removeprefix("www.")
    letter = host[:1].upper() or "?"

    cx, cy, rad = w // 2, 270, 90
    draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], fill="#FFFFFF")
    lf = _font(110)
    bbox = draw.textbbox((0, 0), letter, font=lf)
    draw.text(
        (cx - (bbox[2] - bbox[0]) / 2 - bbox[0], cy - (bbox[3] - bbox[1]) / 2 - bbox[1]),
        letter,
        font=lf,
        fill="#14213D",
    )

    hf = _font(56)
    bbox = draw.textbbox((0, 0), host, font=hf)
    draw.text(((w - (bbox[2] - bbox[0])) / 2, 430), host, font=hf, fill="#FFFFFF")

    if title:
        sub = title if len(title) <= 60 else title[:57] + "..."
        sf = _font(30)
        bbox = draw.textbbox((0, 0), sub, font=sf)
        draw.text(((w - (bbox[2] - bbox[0])) / 2, 520), sub, font=sf, fill="#C9D6FF")

    nf = _font(24)
    note = "Live preview unavailable for this site"
    bbox = draw.textbbox((0, 0), note, font=nf)
    draw.text(((w - (bbox[2] - bbox[0])) / 2, 700), note, font=nf, fill="#9FB3FF")
    return img


# --------------------------------------------------------------------------- #
# Public entry point
# --------------------------------------------------------------------------- #
def generate_preview(url: str) -> Tuple[str, Optional[str], str]:
    """Return (preview_filename, title, preview_type). Never raises for fetch failures."""
    title: Optional[str] = None

    # 1. Real browser screenshot
    shot, title = _playwright_screenshot(url)
    if shot:
        img = _image_from_bytes(shot)
        if img:
            return _save_image(img), title, "screenshot"

    # 2. Screenshot service
    if config.USE_THUMIO_FALLBACK:
        data = _thumio_screenshot(url)
        if data:
            img = _image_from_bytes(data)
            if img:
                meta_title, _ = (None, None) if title else _fetch_metadata(url)
                return _save_image(img), title or meta_title, "thumbnail"

    # 3. Open Graph image
    meta_title, og_image = _fetch_metadata(url)
    title = title or meta_title
    if og_image:
        data = _download_image(og_image)
        img = _image_from_bytes(data) if data else None
        if img:
            return _save_image(img), title, "og_image"

    # 4. Placeholder
    return _save_image(_placeholder(url, title)), title, "placeholder"
