import json
from datetime import datetime
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import LocalResearchRecord, ResearchImage, ResearchSource


RESEARCH_DIRECTORY = Path(__file__).resolve().parents[1] / "research"


def _read_dataset(name: str) -> dict:
    return json.loads((RESEARCH_DIRECTORY / name).read_text(encoding="utf-8"))


def import_research_data(db: Session) -> None:
    accessed_at = datetime.fromisoformat(_read_dataset("sources.json")["accessed_date"])
    source_rows = _read_dataset("sources.json")["sources"]
    sources_by_url: dict[str, ResearchSource] = {}
    for row in source_rows:
        source = db.query(ResearchSource).filter_by(url=row["url"]).first()
        if source is None:
            source = ResearchSource(
                url=row["url"],
                title=row["title"],
                publisher=row["publisher"],
                source_type=row["source_type"],
                coverage=row["coverage"],
                notes=row["notes"],
                accessed_at=accessed_at,
            )
            db.add(source)
            db.flush()
        sources_by_url[source.url] = source

    record_rows = list(_read_dataset("records.json")["records"])
    for row in _read_dataset("products.json")["records"]:
        record_rows.append({
            "slug": row["slug"],
            "record_type": "product_reference",
            "title": row["product"],
            "description": row["description"],
            "location": row["evidence_scope"],
            "verification_status": row["verification_status"],
            "source_url": row["source_urls"][0],
            "public_listing_permission": True,
            "metadata": {
                "category": row["category"],
                "regional_relevance": row["regional_relevance"],
                "typical_unit": row["typical_unit"],
                "seasonality": row["seasonality"],
                "price": row["price"],
                "price_currency": row["price_currency"],
                "price_source": row["price_source"],
                "price_observed_date": row["price_observed_date"],
                "price_type": row["price_type"],
            },
        })

    for row in record_rows:
        if db.query(LocalResearchRecord.id).filter_by(slug=row["slug"]).first():
            continue
        source = sources_by_url.get(row["source_url"])
        if source is None:
            raise ValueError(f"Research source is missing for record {row['slug']}")
        db.add(LocalResearchRecord(
            slug=row["slug"],
            record_type=row["record_type"],
            title=row["title"],
            description=row["description"],
            location=row.get("location", ""),
            verification_status=row.get("verification_status", "unverified"),
            publication_status="pending",
            public_listing_permission=row.get("public_listing_permission", False),
            is_demo=False,
            source_id=source.id,
            metadata_json=json.dumps(row.get("metadata", {}), ensure_ascii=False),
            last_verified_at=accessed_at,
        ))

    for row in _read_dataset("images.json")["images"]:
        if db.query(ResearchImage.id).filter_by(slug=row["slug"]).first():
            continue
        source = sources_by_url.get(row["source_page"])
        if source is None:
            raise ValueError(f"Research source is missing for image {row['slug']}")
        db.add(ResearchImage(
            slug=row["slug"],
            title=row["title"],
            local_asset=row["local_asset"],
            image_url=row["image_url"],
            source_page=row["source_page"],
            photographer=row["photographer"],
            license=row["license"],
            license_url=row.get("license_url"),
            attribution=row["attribution"],
            subject=row["subject"],
            image_type=row["image_type"],
            local_to_peja=row["local_to_peja"],
            usage_rights_confirmed=row["usage_rights_confirmed"],
            display_publicly=row["display_publicly"],
            source_id=source.id,
            last_verified_at=accessed_at,
        ))
    db.commit()
