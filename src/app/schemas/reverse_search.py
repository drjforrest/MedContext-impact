from __future__ import annotations

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel


class ReverseSearchMatch(BaseModel):
    source: str
    url: str
    title: Optional[str] = None
    snippet: Optional[str] = None
    confidence: float
    discovered_at: Optional[datetime] = None
    metadata: dict[str, Any] | None = None


class ReverseSearchJobResponse(BaseModel):
    job_id: UUID
    image_id: UUID
    status: str
    detail: Optional[str] = None
    query_hash: Optional[str] = None
    queued_at: datetime


class ReverseSearchResult(BaseModel):
    job_id: UUID
    image_id: UUID
    status: str
    queried_at: datetime
    query_hash: Optional[str] = None
    providers: list[str] | None = None
    matches: list[ReverseSearchMatch]
