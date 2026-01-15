from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class SubmissionResponse(BaseModel):
    image_id: UUID
    status: str = "accepted"
    detail: Optional[str] = None


class JobResponse(BaseModel):
    job_id: UUID
    status: str = "queued"
    detail: Optional[str] = None


class IntegrityWeightsResponse(BaseModel):
    plausibility: float
    genealogy_consistency: float
    source_reputation: float


class IntegrityScoreResponse(BaseModel):
    plausibility: Optional[float] = None
    genealogy_consistency: Optional[float] = None
    source_reputation: Optional[float] = None
    weights: IntegrityWeightsResponse
    score: float
