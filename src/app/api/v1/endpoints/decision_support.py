from uuid import UUID, uuid4

from fastapi import APIRouter, Query

from app.schemas.common import JobResponse

router = APIRouter()


@router.post("/assess/{image_id}", response_model=JobResponse)
async def assess_image(image_id: UUID) -> JobResponse:
    return JobResponse(job_id=uuid4(), detail=f"assessment queued for {image_id}")


@router.get("/recommendation/{image_id}", response_model=JobResponse)
async def get_recommendation(
    image_id: UUID, audience: str = Query("general")
) -> JobResponse:
    return JobResponse(
        job_id=uuid4(),
        status="completed",
        detail=f"recommendation ready for {image_id} ({audience})",
    )


@router.get("/summary/{image_id}", response_model=JobResponse)
async def get_executive_summary(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"summary ready for {image_id}"
    )
