from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ProvenanceManifest(Base):
    __tablename__ = "provenance_manifests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    image_id = Column(
        UUID(as_uuid=True), ForeignKey("image_submissions.id"), nullable=True
    )
    image_hash = Column(String, unique=True, index=True, nullable=False)
    manifest_label = Column(String, nullable=True)
    manifest_json = Column(JSONB, nullable=True)
    signature_status = Column(String, nullable=True)
    validation_state = Column(String, nullable=True)
    validation_results = Column(JSONB, nullable=True)
    source_url = Column(Text, nullable=True)
    blockchain_tx_hash = Column(String, unique=True, nullable=True)
    blockchain_network = Column(String, nullable=True)
    blockchain_anchored_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    image = relationship("ImageSubmission", back_populates="provenance_manifests")
    blocks = relationship("ProvenanceBlock", back_populates="manifest")


class ProvenanceBlock(Base):
    __tablename__ = "provenance_blocks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    manifest_id = Column(
        UUID(as_uuid=True), ForeignKey("provenance_manifests.id"), nullable=False
    )
    block_number = Column(Integer, nullable=False)
    previous_hash = Column(String, nullable=True)
    block_hash = Column(String, nullable=False)
    observation_type = Column(String, nullable=False)
    observation_data = Column(JSONB, nullable=False)
    recorded_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    manifest = relationship("ProvenanceManifest", back_populates="blocks")
