import { previewSrc } from "../api.js";

const TYPE_LABEL = {
  screenshot: "Live screenshot",
  thumbnail: "Screenshot",
  og_image: "Site image",
  placeholder: "Preview unavailable",
};

function hostOf(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, "");
  } catch {
    return url;
  }
}

function formatDate(iso) {
  // The API returns UTC timestamps; make sure the browser treats them as UTC.
  const d = new Date(/Z|[+-]\d\d:?\d\d$/.test(iso) ? iso : iso + "Z");
  return d.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export default function PreviewCard({ site, onDelete, large = false }) {
  const host = hostOf(site.url);
  return (
    <article className={`frame card ${large ? "card-large" : ""}`}>
      <div className="frame-bar">
        <span /><span /><span />
        <a className="frame-url" href={site.url} target="_blank" rel="noopener noreferrer" title={site.url}>
          {host}
        </a>
      </div>

      <a className="shot" href={site.url} target="_blank" rel="noopener noreferrer">
        <img src={previewSrc(site.preview_url)} alt={`Preview of ${host}`} loading="lazy" />
      </a>

      <div className="card-info">
        <h3 title={site.title || host}>{site.title || host}</h3>
        <a className="card-link" href={site.url} target="_blank" rel="noopener noreferrer" title={site.url}>
          {site.url}
        </a>
        <div className="card-meta">
          <span className={`tag tag-${site.preview_type}`}>{TYPE_LABEL[site.preview_type] || site.preview_type}</span>
          <span className="muted small">{formatDate(site.created_at)}</span>
          {onDelete && (
            <button className="btn link danger" onClick={() => onDelete(site)} aria-label={`Delete ${host}`}>
              Delete
            </button>
          )}
        </div>
      </div>
    </article>
  );
}
