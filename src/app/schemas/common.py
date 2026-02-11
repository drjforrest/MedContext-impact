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
