from uuid import UUID, uuid4

from fastapi import APIRouter

from app.schemas.common import JobResponse

router = APIRouter()


@router.post("/analyze/{image_id}", response_model=JobResponse)
async def analyze_claims(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), detail=f"semantic analysis queued for {image_id}"
    )


@router.get("/clusters/{image_id}", response_model=JobResponse)
async def get_semantic_clusters(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"clusters ready for {image_id}"
    )
