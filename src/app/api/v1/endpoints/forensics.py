from fastapi import APIRouter, Depends, File, UploadFile

from app.core.modules import require_module
from app.forensics.service import run_forensics
from app.schemas.common import JobResponse


router = APIRouter()


@router.post(
    "/analyze",
    response_model=JobResponse,
    dependencies=[Depends(require_module("forensics"))],
)
async def analyze_forensics(file: UploadFile = File(...)) -> JobResponse:
    image_bytes = await file.read()
    result = run_forensics(image_bytes=image_bytes)
    return JobResponse(
        job_id=result["job_id"], status=result["status"], detail=result["detail"]
    )
