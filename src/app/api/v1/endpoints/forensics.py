from fastapi import APIRouter, File, UploadFile

from app.forensics.deepfake import run_deepfake_detection
from app.forensics.service import run_forensics
from app.schemas.common import JobResponse
from app.schemas.forensics import DeepfakeDetectionResponse


router = APIRouter()


@router.post("/analyze", response_model=JobResponse)
async def analyze_forensics(file: UploadFile = File(...)) -> JobResponse:
    image_bytes = await file.read()
    result = run_forensics(image_bytes=image_bytes)
    return JobResponse(
        job_id=result["job_id"], status=result["status"], detail=result["detail"]
    )


@router.post("/deepfake", response_model=DeepfakeDetectionResponse)
async def analyze_deepfake(file: UploadFile = File(...)) -> DeepfakeDetectionResponse:
    image_bytes = await file.read()
    result = run_deepfake_detection(image_bytes=image_bytes)
    return DeepfakeDetectionResponse(
        final_verdict=result.final_verdict,
        confidence=result.confidence,
        layer_1=result.layer_1.__dict__,
        layer_2=result.layer_2.__dict__,
        layer_3=result.layer_3.__dict__,
    )
