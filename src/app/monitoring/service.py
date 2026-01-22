from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timezone
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import MonitoringItem, MonitoringSource
from app.monitoring.facebook import ingest_post
from app.monitoring.reddit import RedditClient, RedditClientError, parse_reddit_list
from app.monitoring.twitter import ingest_tweet
from app.monitoring.telegram import process_update
from app.monitoring.whatsapp import process_webhook
from app.schemas.monitoring import MonitoringIngestResponse


def ingest_monitoring_payload(payload: dict[str, Any]) -> MonitoringIngestResponse:
    """Route payloads to platform-specific stubs."""
    source = str(payload.get("source", "unknown")).lower()
    if source == "telegram":
        result = process_update(payload)
    elif source == "whatsapp":
        result = process_webhook(payload)
    elif source == "facebook":
        result = ingest_post(payload)
    elif source in {"twitter", "x"}:
        result = ingest_tweet(payload)
    elif "update_id" in payload and ("message" in payload or "channel_post" in payload):
        result = process_update(payload)
    else:
        return MonitoringIngestResponse(
            status="rejected",
            detail="unknown source; expected telegram/whatsapp/facebook/twitter/x",
            metadata={"payload_keys": list(payload.keys())},
        )

    return MonitoringIngestResponse(
        status=result.status, detail=result.detail, metadata=result.metadata
    )


def ensure_reddit_sources(db: Session) -> list[MonitoringSource]:
    sources: list[MonitoringSource] = []
    subreddits = parse_reddit_list(settings.reddit_subreddits)
    keywords = parse_reddit_list(settings.reddit_keywords)
    for subreddit in subreddits:
        sources.append(
            _get_or_create_source(
                db, platform="reddit", source_type="subreddit", value=subreddit
            )
        )
    for keyword in keywords:
        sources.append(
            _get_or_create_source(
                db, platform="reddit", source_type="keyword", value=keyword
            )
        )
    return sources


logger = logging.getLogger(__name__)


def poll_reddit(
    db: Session, *, source_ids: Iterable[str] | None = None, limit: int = 25
) -> tuple[int, int]:
    try:
        client = RedditClient()
    except RedditClientError as e:
        logger.warning("Failed to initialize RedditClient: %s", e)
        return 0, 0

    sources = ensure_reddit_sources(db)
    if source_ids:
        allowed = {str(source_id) for source_id in source_ids}
        sources = [source for source in sources if str(source.id) in allowed]

    ingested = 0
    for source in sources:
        if not source.is_active:
            continue
        if source.source_type == "subreddit":
            items = client.fetch_subreddit_posts(source.value, limit=limit)
        else:
            items = client.search_keyword_posts(source.value, limit=limit)
        ingested += _persist_items(db, source, items)
    return len(sources), ingested


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


def start_monitoring_polling_loop(get_db_session) -> None:
    if not settings.enable_monitoring_polling:
        return

    interval_seconds = max(settings.reddit_poll_interval_minutes, 1) * 60

    def _loop():
        while True:
            try:
                db = next(get_db_session())
                try:
                    poll_reddit(db)
                finally:
                    db.close()
            except Exception as e:
                logger.exception("Monitoring polling loop failed: %s", e)
            time.sleep(interval_seconds)

    thread = threading.Thread(target=_loop, name="monitoring-poll", daemon=True)
    thread.start()
    thread.start()
