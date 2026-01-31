from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import MonitoringItem, MonitoringSource
from app.monitoring.telegram import process_update
from app.schemas.monitoring import MonitoringIngestResponse


def ingest_monitoring_payload(payload: dict[str, Any]) -> MonitoringIngestResponse:
    """Route payloads to Telegram integration."""
    source = str(payload.get("source", "unknown")).lower()

    # Check if it's a Telegram payload
    if source == "telegram" or (
        "update_id" in payload and ("message" in payload or "channel_post" in payload)
    ):
        result = process_update(payload)
        return MonitoringIngestResponse(
            status=result.status, detail=result.detail, metadata=result.metadata
        )

    # Reject non-Telegram payloads
    return MonitoringIngestResponse(
        status="rejected",
        detail="unknown source; only Telegram is supported",
        metadata={"payload_keys": list(payload.keys()), "source": source},
    )


logger = logging.getLogger(__name__)


def list_recent_items(db: Session, *, limit: int = 50) -> list[MonitoringItem]:
    return (
        db.execute(
            select(MonitoringItem)
            .order_by(MonitoringItem.ingested_at.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )


def _get_or_create_source(
    db: Session, *, platform: str, source_type: str, value: str
) -> MonitoringSource:
    existing = (
        db.execute(
            select(MonitoringSource).where(
                MonitoringSource.platform == platform,
                MonitoringSource.source_type == source_type,
                MonitoringSource.value == value,
            )
        )
        .scalars()
        .first()
    )
    if existing:
        return existing
    source = MonitoringSource(
        platform=platform, source_type=source_type, value=value, is_active=True
    )
    db.add(source)
    try:
        db.commit()
        db.refresh(source)
        return source
    except IntegrityError:
        db.rollback()
        return (
            db.execute(
                select(MonitoringSource).where(
                    MonitoringSource.platform == platform,
                    MonitoringSource.source_type == source_type,
                    MonitoringSource.value == value,
                )
            )
            .scalars()
            .first()
        )


def _persist_items(
    db: Session, source: MonitoringSource, items: list[dict[str, Any]]
) -> int:
    ingested = 0
    for item in items:
        existing = (
            db.execute(
                select(MonitoringItem).where(
                    MonitoringItem.platform == source.platform,
                    MonitoringItem.post_id == item["post_id"],
                )
            )
            .scalars()
            .first()
        )
        if existing:
            continue
        monitoring_item = MonitoringItem(
            source_id=source.id,
            platform=source.platform,
            post_id=item["post_id"],
            title=item.get("title"),
            body=item.get("body"),
            author=item.get("author"),
            subreddit=item.get("subreddit"),
            created_utc=item.get("created_utc"),
            url=item.get("url"),
            media_urls=item.get("media_urls"),
            context_text=item.get("context_text"),
            raw_payload=item.get("raw_payload"),
            ingested_at=datetime.now(tz=timezone.utc),
        )
        db.add(monitoring_item)
        ingested += 1
    if ingested:
        db.commit()
    return ingested
