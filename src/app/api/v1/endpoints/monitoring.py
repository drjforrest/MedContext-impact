from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.monitoring.service import (
    ingest_monitoring_payload,
    list_recent_items,
    poll_reddit,
)
from app.schemas.monitoring import (
    MonitoringIngestResponse,
    MonitoringItemResponse,
    MonitoringItemsResponse,
    MonitoringPollRequest,
    MonitoringPollResponse,
)

router = APIRouter()


@router.post("/ingest", response_model=MonitoringIngestResponse)
def ingest_monitoring(payload: dict[str, Any]) -> MonitoringIngestResponse:
    return ingest_monitoring_payload(payload)


@router.post("/telegram", response_model=MonitoringIngestResponse)
def ingest_telegram(payload: dict[str, Any]) -> MonitoringIngestResponse:
    enriched = dict(payload)
    enriched.setdefault("source", "telegram")
    return ingest_monitoring_payload(enriched)


@router.post("/poll", response_model=MonitoringPollResponse)
def poll_monitoring(
    payload: MonitoringPollRequest, db: Session = Depends(get_db)
) -> MonitoringPollResponse:
    sources, ingested = poll_reddit(db, source_ids=payload.source_ids)
    return MonitoringPollResponse(
        status="ok", polled_sources=sources, ingested_items=ingested
    )


@router.get("/items", response_model=MonitoringItemsResponse)
def list_monitoring_items(
    db: Session = Depends(get_db), limit: int = 50
) -> MonitoringItemsResponse:
    items = list_recent_items(db, limit=limit)
    return MonitoringItemsResponse(
        items=[
            MonitoringItemResponse(
                id=item.id,
                source_id=item.source_id,
                platform=item.platform,
                post_id=item.post_id,
                title=item.title,
                body=item.body,
                author=item.author,
                subreddit=item.subreddit,
                created_utc=item.created_utc,
                url=item.url,
                media_urls=item.media_urls,
                context_text=item.context_text,
                ingested_at=item.ingested_at,
            )
            for item in items
        ]
    )
