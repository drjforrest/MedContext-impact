from uuid import uuid4

import hashlib
import imghdr
import json

from fastapi import APIRouter, Depends, File, Form, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ImageSubmission, MedGemmaAnalysis, SubmissionContext
from app.db.session import get_db
from app.orchestrator.agent import MedContextAgent
from app.schemas.common import SubmissionResponse
from app.schemas.orchestrator import AgentRunResponse

router = APIRouter()


@router.post("/web", response_model=SubmissionResponse)
async def handle_web_upload(
    file: UploadFile = File(...),
    context: str = Form(...),
) -> SubmissionResponse:
    return SubmissionResponse(image_id=uuid4(), detail="web upload accepted")


@router.post("/extension", response_model=SubmissionResponse)
async def handle_extension_submission(
    file: UploadFile = File(...),
    context: str = Form(...),
) -> SubmissionResponse:
    return SubmissionResponse(image_id=uuid4(), detail="extension upload accepted")


@router.post("/whatsapp", response_model=SubmissionResponse)
async def handle_whatsapp_webhook(payload: dict) -> SubmissionResponse:
    return SubmissionResponse(image_id=uuid4(), detail="whatsapp payload accepted")


@router.post("/agentic", response_model=AgentRunResponse)
async def ingest_and_run_agent(
    file: UploadFile = File(...),
    context: str = Form(...),
    db: Session = Depends(get_db),
) -> AgentRunResponse:
    image_id = uuid4()
    image_bytes = await file.read()
    image_format = imghdr.what(None, h=image_bytes) or "jpeg"
    if image_format == "jpg":
        image_format = "jpeg"
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    mime_type = file.content_type or f"image/{image_format}"

    submission = ImageSubmission(
        id=image_id,
        source_channel="agentic",
        user_id=None,
        image_hash=image_hash,
        image_path=None,
        file_size=len(image_bytes),
        mime_type=mime_type,
        image_format=image_format,
        width=None,
        height=None,
        orientation_corrected=False,
        metadata_extracted=False,
    )
    submission_context = SubmissionContext(
        image_id=image_id,
        surrounding_text=context,
        claimed_condition=None,
        claimed_origin=None,
        source_url=None,
        source_whatsapp_group=None,
        language_code="en",
    )
    db.add(submission)
    db.add(submission_context)
    db.commit()

    agent = MedContextAgent()
    result = agent.run(image_bytes=image_bytes, image_id=str(image_id))

    triage_payload = result.triage
    triage_json = json.dumps(triage_payload, default=str, ensure_ascii=True)
    clinical_impression = None
    if isinstance(triage_payload, dict):
        clinical_impression = triage_payload.get("primary_findings")
    analysis = MedGemmaAnalysis(
        image_id=image_id,
        key_findings=triage_json,
        clinical_impression=clinical_impression,
        claimed_condition_analyzed=bool(context),
        model_version=settings.medgemma_hf_model,
    )
    db.add(analysis)
    db.commit()

    return AgentRunResponse(
        triage={"context": context, "triage": result.triage},
        tool_results=result.tool_results,
        synthesis=result.synthesis,
    )
