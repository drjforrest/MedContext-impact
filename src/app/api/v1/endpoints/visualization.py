from uuid import UUID, uuid4

from fastapi import APIRouter

from app.schemas.common import JobResponse

router = APIRouter()


@router.get("/distribution/{image_id}", response_model=JobResponse)
async def get_distribution_chart(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"distribution ready for {image_id}"
    )


@router.get("/timeline/{image_id}", response_model=JobResponse)
async def get_timeline(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"timeline ready for {image_id}"
    )


@router.get("/confidence/{image_id}", response_model=JobResponse)
async def get_confidence_metrics(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"confidence ready for {image_id}"
    )
