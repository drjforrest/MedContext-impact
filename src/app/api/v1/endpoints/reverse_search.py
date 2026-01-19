from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from app.reverse_search.service import get_reverse_search_results, run_reverse_search
from app.schemas.reverse_search import ReverseSearchJobResponse, ReverseSearchResult

router = APIRouter()


@router.post("/search/{image_id}", response_model=ReverseSearchJobResponse)
async def trigger_reverse_search(
    image_id: UUID, file: UploadFile | None = File(default=None)
) -> ReverseSearchJobResponse:
    image_bytes = await file.read() if file else b""
    return run_reverse_search(image_id=image_id, image_bytes=image_bytes)


@router.get("/results/{image_id}", response_model=ReverseSearchResult)
async def get_search_results(image_id: UUID) -> ReverseSearchResult:
    return get_reverse_search_results(image_id=image_id)
