from uuid import UUID

from fastapi import APIRouter

from app.reverse_search.service import get_reverse_search_results, run_reverse_search
from app.schemas.common import JobResponse

router = APIRouter()


@router.post("/search/{image_id}", response_model=JobResponse)
async def trigger_reverse_search(image_id: UUID) -> JobResponse:
    result = run_reverse_search(image_id=image_id, image_bytes=b"")
    return JobResponse(
        job_id=result["job_id"], status=result["status"], detail=result["detail"]
    )


@router.get("/results/{image_id}", response_model=JobResponse)
async def get_search_results(image_id: UUID) -> JobResponse:
    result = get_reverse_search_results(image_id=image_id)
    return JobResponse(
        job_id=result["job_id"], status=result["status"], detail=result["detail"]
    )
