import json
from datetime import datetime
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import require_role
from app.database import get_db
from app.models import (
    LocalResearchRecord,
    Product,
    ResearchImage,
    ResearchSource,
    Role,
    User,
)

router = APIRouter(prefix="/research", tags=["local research"])
admin_router = APIRouter(prefix="/research/admin", tags=["local research admin"])
ASSET_DIRECTORY = Path(__file__).resolve().parents[2] / "assets"

VerificationStatus = Literal[
    "verified", "publicly_documented", "unverified", "demonstration_data"
]
PublicationStatus = Literal["pending", "approved", "rejected"]


class ResearchRecordUpdate(BaseModel):
    record_type: Literal[
        "business", "farm", "regional_fact", "location", "food_tradition",
        "historical_market_reference", "food_venue", "product_reference",
    ] | None = None
    title: str | None = Field(default=None, min_length=2, max_length=250)
    description: str | None = Field(default=None, min_length=2)
    location: str | None = Field(default=None, max_length=200)
    verification_status: VerificationStatus | None = None
    publication_status: PublicationStatus | None = None
    public_listing_permission: bool | None = None
    metadata: dict | None = None


class ResearchSourceUpdate(BaseModel):
    url: HttpUrl | None = None
    title: str | None = Field(default=None, min_length=2, max_length=300)
    publisher: str | None = Field(default=None, max_length=200)
    coverage: str | None = None
    notes: str | None = None


class ResearchImageUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=250)
    photographer: str | None = Field(default=None, max_length=200)
    license: str | None = Field(default=None, min_length=2, max_length=100)
    license_url: HttpUrl | None = None
    attribution: str | None = Field(default=None, min_length=2, max_length=500)
    subject: str | None = Field(default=None, min_length=2, max_length=500)
    usage_rights_confirmed: bool | None = None
    display_publicly: bool | None = None


def _source_out(source: ResearchSource) -> dict:
    return {
        "id": source.id,
        "url": source.url,
        "title": source.title,
        "publisher": source.publisher,
        "source_type": source.source_type,
        "coverage": source.coverage,
        "notes": source.notes,
        "accessed_at": source.accessed_at,
    }


def _record_out(record: LocalResearchRecord, source: ResearchSource) -> dict:
    return {
        "id": record.id,
        "slug": record.slug,
        "record_type": record.record_type,
        "title": record.title,
        "description": record.description,
        "location": record.location,
        "verification_status": record.verification_status,
        "publication_status": record.publication_status,
        "public_listing_permission": record.public_listing_permission,
        "is_demo": record.is_demo,
        "metadata": json.loads(record.metadata_json or "{}"),
        "last_verified_at": record.last_verified_at,
        "updated_at": record.updated_at,
        "source": _source_out(source),
    }


def _image_out(image: ResearchImage, source: ResearchSource) -> dict:
    asset_path = image.local_asset.replace("\\", "/")
    if asset_path.startswith("assets/"):
        asset_path = "/" + asset_path
    return {
        "id": image.id,
        "slug": image.slug,
        "title": image.title,
        "local_asset": asset_path,
        "image_url": image.image_url,
        "source_page": image.source_page,
        "photographer": image.photographer,
        "license": image.license,
        "license_url": image.license_url,
        "attribution": image.attribution,
        "subject": image.subject,
        "image_type": image.image_type,
        "local_to_peja": image.local_to_peja,
        "usage_rights_confirmed": image.usage_rights_confirmed,
        "display_publicly": image.display_publicly,
        "last_verified_at": image.last_verified_at,
        "source": _source_out(source),
    }


@router.get("/public")
def public_research(db: Session = Depends(get_db)):
    rows = db.query(LocalResearchRecord, ResearchSource).join(
        ResearchSource, LocalResearchRecord.source_id == ResearchSource.id
    ).filter(
        LocalResearchRecord.is_active.is_(True),
        LocalResearchRecord.publication_status == "approved",
        LocalResearchRecord.public_listing_permission.is_(True),
    ).order_by(LocalResearchRecord.record_type, LocalResearchRecord.title).all()
    return [_record_out(record, source) for record, source in rows]


@router.get("/images/public")
def public_images(db: Session = Depends(get_db)):
    rows = db.query(ResearchImage, ResearchSource).join(
        ResearchSource, ResearchImage.source_id == ResearchSource.id
    ).filter(
        ResearchImage.is_active.is_(True),
        ResearchImage.display_publicly.is_(True),
        ResearchImage.usage_rights_confirmed.is_(True),
    ).order_by(ResearchImage.image_type, ResearchImage.title).all()
    return [_image_out(image, source) for image, source in rows]


@router.get("/images/{slug}/file")
def public_image_file(slug: str, db: Session = Depends(get_db)):
    image = db.query(ResearchImage).filter(
        ResearchImage.slug == slug,
        ResearchImage.is_active.is_(True),
        ResearchImage.display_publicly.is_(True),
        ResearchImage.usage_rights_confirmed.is_(True),
    ).first()
    if image is None:
        raise HTTPException(status_code=404, detail="Image is not approved for public display")
    relative_path = image.local_asset.replace("\\", "/")
    if relative_path.startswith("assets/"):
        relative_path = relative_path.removeprefix("assets/")
    asset_path = (ASSET_DIRECTORY / relative_path).resolve()
    if not asset_path.is_relative_to(ASSET_DIRECTORY.resolve()):
        raise HTTPException(status_code=404, detail="Image asset not found")
    if not asset_path.is_file():
        raise HTTPException(status_code=404, detail="Image asset not found")
    return FileResponse(asset_path)


@admin_router.get("/summary")
def research_summary(
    user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    businesses = db.query(LocalResearchRecord).filter(
        LocalResearchRecord.is_active.is_(True),
        LocalResearchRecord.record_type.in_(("business", "farm")),
    )
    return {
        "total_researched_businesses": businesses.count(),
        "verified_businesses": businesses.filter(
            LocalResearchRecord.verification_status == "verified"
        ).count(),
        "publicly_documented_businesses": businesses.filter(
            LocalResearchRecord.verification_status == "publicly_documented"
        ).count(),
        "demonstration_records": (
            db.query(LocalResearchRecord).filter(LocalResearchRecord.is_demo.is_(True)).count()
            + db.query(User).filter(User.is_demo.is_(True)).count()
            + db.query(Product).filter(Product.is_demo.is_(True)).count()
        ),
        "products_with_regional_information": db.query(LocalResearchRecord).filter(
            LocalResearchRecord.is_active.is_(True),
            LocalResearchRecord.record_type == "product_reference",
            LocalResearchRecord.verification_status.in_(("verified", "publicly_documented")),
        ).count(),
        "images_with_confirmed_rights": db.query(ResearchImage).filter(
            ResearchImage.is_active.is_(True),
            ResearchImage.usage_rights_confirmed.is_(True),
        ).count(),
        "records_requiring_review": db.query(LocalResearchRecord).filter(
            LocalResearchRecord.is_active.is_(True),
            LocalResearchRecord.publication_status == "pending",
        ).count(),
        "images_requiring_rights_review": db.query(ResearchImage).filter(
            ResearchImage.is_active.is_(True),
            ResearchImage.usage_rights_confirmed.is_(False),
        ).count(),
    }


@admin_router.get("/records")
def list_research_records(
    record_type: str | None = None,
    publication_status: PublicationStatus | None = None,
    search: str | None = Query(default=None, max_length=120),
    user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(LocalResearchRecord, ResearchSource).join(
        ResearchSource, LocalResearchRecord.source_id == ResearchSource.id
    ).filter(LocalResearchRecord.is_active.is_(True))
    if record_type:
        query = query.filter(LocalResearchRecord.record_type == record_type)
    if publication_status:
        query = query.filter(LocalResearchRecord.publication_status == publication_status)
    if search:
        term = f"%{search}%"
        query = query.filter(
            LocalResearchRecord.title.ilike(term)
            | LocalResearchRecord.description.ilike(term)
            | LocalResearchRecord.location.ilike(term)
        )
    return [
        _record_out(record, source)
        for record, source in query.order_by(LocalResearchRecord.title).limit(300).all()
    ]


@admin_router.patch("/records/{record_id}")
def update_research_record(
    record_id: int,
    payload: ResearchRecordUpdate,
    user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    record = db.get(LocalResearchRecord, record_id)
    if record is None or not record.is_active:
        raise HTTPException(status_code=404, detail="Research record not found")
    updates = payload.model_dump(exclude_unset=True)
    metadata = updates.pop("metadata", None)
    for key, value in updates.items():
        setattr(record, key, value)
    if metadata is not None:
        record.metadata_json = json.dumps(metadata, ensure_ascii=False)
    if payload.verification_status in {"verified", "publicly_documented"}:
        record.last_verified_at = datetime.utcnow()
    db.commit()
    db.refresh(record)
    source = db.get(ResearchSource, record.source_id)
    return _record_out(record, source)


@admin_router.patch("/sources/{source_id}")
def update_research_source(
    source_id: int,
    payload: ResearchSourceUpdate,
    user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    source = db.get(ResearchSource, source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Research source not found")
    updates = payload.model_dump(exclude_unset=True)
    old_url = source.url
    for key, value in updates.items():
        setattr(source, key, str(value) if key == "url" and value else value)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=409, detail="That source URL is already registered") from exc
    if source.url != old_url:
        db.query(ResearchImage).filter(
            ResearchImage.source_id == source.id
        ).update({"source_page": source.url}, synchronize_session=False)
        db.commit()
    db.refresh(source)
    return _source_out(source)


@admin_router.delete("/records/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_research_record(
    record_id: int,
    user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    record = db.get(LocalResearchRecord, record_id)
    if record is None or not record.is_active:
        raise HTTPException(status_code=404, detail="Research record not found")
    record.is_active = False
    record.publication_status = "rejected"
    db.commit()
    return None


@admin_router.get("/images")
def list_research_images(
    search: str | None = Query(default=None, max_length=120),
    user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    query = db.query(ResearchImage, ResearchSource).join(
        ResearchSource, ResearchImage.source_id == ResearchSource.id
    ).filter(ResearchImage.is_active.is_(True))
    if search:
        term = f"%{search}%"
        query = query.filter(
            ResearchImage.title.ilike(term)
            | ResearchImage.photographer.ilike(term)
            | ResearchImage.license.ilike(term)
        )
    return [
        _image_out(image, source)
        for image, source in query.order_by(ResearchImage.title).limit(300).all()
    ]


@admin_router.patch("/images/{image_id}")
def update_research_image(
    image_id: int,
    payload: ResearchImageUpdate,
    user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    image = db.get(ResearchImage, image_id)
    if image is None or not image.is_active:
        raise HTTPException(status_code=404, detail="Research image not found")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(image, key, str(value) if key == "license_url" and value else value)
    if not image.usage_rights_confirmed:
        image.display_publicly = False
    db.commit()
    db.refresh(image)
    source = db.get(ResearchSource, image.source_id)
    return _image_out(image, source)


@admin_router.delete("/images/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_research_image(
    image_id: int,
    user=Depends(require_role(Role.ADMIN)),
    db: Session = Depends(get_db),
):
    image = db.get(ResearchImage, image_id)
    if image is None or not image.is_active:
        raise HTTPException(status_code=404, detail="Research image not found")
    image.is_active = False
    image.display_publicly = False
    db.commit()
    return None
