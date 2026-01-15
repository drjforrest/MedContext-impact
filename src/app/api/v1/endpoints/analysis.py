from uuid import UUID, uuid4

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.clinical.medgemma_client import MedGemmaClient, MedGemmaClientError
from app.schemas.common import JobResponse
from app.schemas.medgemma import MedGemmaResponse

router = APIRouter()


@router.post("/image/{image_id}", response_model=JobResponse)
async def analyze_image(image_id: UUID) -> JobResponse:
    return JobResponse(job_id=uuid4(), detail=f"analysis queued for {image_id}")


@router.get("/analysis/{analysis_id}", response_model=JobResponse)
async def get_analysis(analysis_id: UUID) -> JobResponse:
    return JobResponse(job_id=analysis_id, status="completed")


@router.post("/upload", response_model=MedGemmaResponse)
async def analyze_upload(
    file: UploadFile = File(...),
    prompt: str | None = Form(default=None),
) -> MedGemmaResponse:
    image_bytes = await file.read()
    client = MedGemmaClient()
    try:
        result = client.analyze_image(image_bytes=image_bytes, prompt=prompt)
    except MedGemmaClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return MedGemmaResponse(
        provider=result.provider, model=result.model, output=result.output
    )
