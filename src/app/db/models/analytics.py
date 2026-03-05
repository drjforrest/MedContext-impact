"""Analytics models for run metrics."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID

from app.db.base import Base


class RunEvent(Base):
    """Records each verification run for analytics."""

    __tablename__ = "run_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    started_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    duration_ms = Column(Integer, nullable=False)
    outcome = Column(String(32), nullable=False)  # success | error
    verdict = Column(String(32), nullable=True)  # misinformation | legitimate | unknown
    source_channel = Column(String(64), nullable=False)  # agentic | telegram | api
    ip_address = Column(String(45), nullable=True)  # IPv4 (15) or IPv6 (45)
    error_message = Column(Text, nullable=True)
    created_at = Column(
        DateTime,
        default=lambda _ctx=None: datetime.now(timezone.utc),
        nullable=False,
    )
