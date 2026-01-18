from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class MonitoringIngestResponse(BaseModel):
    status: str
    detail: Optional[str] = None
    metadata: dict[str, Any]


class MonitoringPollRequest(BaseModel):
    source_ids: list[UUID] | None = None


class MonitoringPollResponse(BaseModel):
    status: str
    polled_sources: int
    ingested_items: int


class MonitoringItemResponse(BaseModel):
    id: UUID
    source_id: UUID | None
    platform: str
    post_id: str
    title: str | None
    body: str | None
    author: str | None
    subreddit: str | None
    created_utc: datetime | None
    url: str | None
    media_urls: list[str] | None
    context_text: str | None
    ingested_at: datetime


class MonitoringItemsResponse(BaseModel):
    items: list[MonitoringItemResponse]
