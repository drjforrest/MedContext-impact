from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile

from app.core.modules import require_module
from app.reverse_search.service import get_reverse_search_results, run_reverse_search
from app.schemas.reverse_search import ReverseSearchJobResponse, ReverseSearchResult

router = APIRouter()

_guard = Depends(require_module("reverse_search"))


@router.post(
    "/search/{image_id}",
    response_model=ReverseSearchJobResponse,
    dependencies=[_guard],
)
async def trigger_reverse_search(
    image_id: UUID, file: UploadFile | None = File(default=None)
) -> ReverseSearchJobResponse:
    image_bytes = await file.read() if file else b""
    return run_reverse_search(image_id=image_id, image_bytes=image_bytes)


@router.get(
    "/results/{image_id}",
    response_model=ReverseSearchResult,
    dependencies=[_guard],
)
async def get_search_results(image_id: UUID) -> ReverseSearchResult:
    return get_reverse_search_results(image_id=image_id)
