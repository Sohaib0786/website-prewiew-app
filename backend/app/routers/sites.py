from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import config, models, preview, schemas, security
from ..database import get_db

router = APIRouter(prefix="/api/sites", tags=["sites"])


@router.post("", response_model=schemas.SiteOut, status_code=201)
def create_site(
    body: schemas.SiteCreate,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    """Capture a preview of the URL and save both for the current user.

    Declared as a plain `def` so FastAPI runs it in a worker thread; the screenshot
    step is blocking and can take a few seconds.
    """
    try:
        url = preview.validate_public_url(body.url)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    filename, title, preview_type = preview.generate_preview(url)

    site = models.Site(
        user_id=user.id,
        url=url,
        title=title,
        preview_file=filename,
        preview_type=preview_type,
    )
    db.add(site)
    db.commit()
    db.refresh(site)
    return site


@router.get("", response_model=List[schemas.SiteOut])
def list_sites(
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    return (
        db.query(models.Site)
        .filter(models.Site.user_id == user.id)
        .order_by(models.Site.created_at.desc(), models.Site.id.desc())
        .all()
    )


@router.delete("/{site_id}", status_code=204)
def delete_site(
    site_id: int,
    db: Session = Depends(get_db),
    user: models.User = Depends(security.get_current_user),
):
    site = (
        db.query(models.Site)
        .filter(models.Site.id == site_id, models.Site.user_id == user.id)
        .first()
    )
    if not site:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Saved URL not found.")
    path = config.PREVIEW_DIR / site.preview_file
    db.delete(site)
    db.commit()
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
