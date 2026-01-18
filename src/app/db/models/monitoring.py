from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class MonitoringSource(Base):
    __tablename__ = "monitoring_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    platform = Column(String, nullable=False)
    source_type = Column(String, nullable=False)  # subreddit | keyword
    value = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    items = relationship("MonitoringItem", back_populates="source")


class MonitoringItem(Base):
    __tablename__ = "monitoring_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_id = Column(UUID(as_uuid=True), ForeignKey("monitoring_sources.id"))
    platform = Column(String, nullable=False)
    post_id = Column(String, nullable=False)
    title = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    author = Column(String, nullable=True)
    subreddit = Column(String, nullable=True)
    created_utc = Column(DateTime, nullable=True)
    url = Column(Text, nullable=True)
    media_urls = Column(JSONB, nullable=True)
    context_text = Column(Text, nullable=True)
    raw_payload = Column(JSONB, nullable=True)
    ingested_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    source = relationship("MonitoringSource", back_populates="items")
