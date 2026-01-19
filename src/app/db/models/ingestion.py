from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import Base


class ImageSubmission(Base):
    __tablename__ = "image_submissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    source_channel = Column(String, nullable=False)
    user_id = Column(String, index=True, nullable=True)
    image_hash = Column(String, unique=True, index=True, nullable=False)
    image_path = Column(String, nullable=True)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String, nullable=False)
    image_format = Column(String, nullable=False)
    width = Column(Integer, nullable=True)
    height = Column(Integer, nullable=True)
    orientation_corrected = Column(Boolean, default=False, nullable=False)
    metadata_extracted = Column(Boolean, default=False, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    submissions_context = relationship("SubmissionContext", back_populates="image")
    analyses = relationship("MedGemmaAnalysis", back_populates="image")


class SubmissionContext(Base):
    __tablename__ = "submission_contexts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    image_id = Column(
        UUID(as_uuid=True), ForeignKey("image_submissions.id"), nullable=False
    )
    surrounding_text = Column(Text, nullable=True)
    claimed_condition = Column(String, nullable=True)
    claimed_origin = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    source_whatsapp_group = Column(String, nullable=True)
    language_code = Column(String, default="en", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    image = relationship("ImageSubmission", back_populates="submissions_context")


class MedGemmaAnalysis(Base):
    __tablename__ = "medgemma_analyses"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    image_id = Column(
        UUID(as_uuid=True), ForeignKey("image_submissions.id"), nullable=False
    )

    modality = Column(String, nullable=True)
    anatomical_region = Column(String, nullable=True)
    key_findings = Column(Text, nullable=True)
    clinical_impression = Column(Text, nullable=True)
    findings_confidence = Column(Float, nullable=True)

    image_quality_score = Column(Float, nullable=True)
    quality_issues = Column(Text, nullable=True)

    claimed_condition_analyzed = Column(Boolean, default=False, nullable=False)
    claimed_vs_actual_match = Column(Float, nullable=True)
    match_explanation = Column(Text, nullable=True)
    contextual_inconsistencies = Column(Text, nullable=True)

    model_version = Column(String, nullable=False)
    inference_time_ms = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    analyzed_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    image = relationship("ImageSubmission", back_populates="analyses")
