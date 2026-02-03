import hashlib
import imghdr
import io
import json
import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from PIL import Image
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import ImageSubmission, MedGemmaAnalysis, SubmissionContext
from app.db.session import get_db
from app.orchestrator.langgraph_agent import MedContextLangGraphAgent
from app.provenance.service import store_provenance_manifest
from app.schemas.common import SubmissionResponse
from app.schemas.orchestrator import AgentRunResponse

router = APIRouter()
logger = logging.getLogger(__name__)


def _persist_image_bytes(image_id: UUID, image_bytes: bytes, image_format: str) -> Path:
    storage_dir = Path(settings.image_storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    image_path = storage_dir / f"{image_id}.{image_format}"
    image_path.write_bytes(image_bytes)
    return image_path.resolve()


def _cleanup_image_file(image_path: Path) -> None:
    try:
        if image_path.exists():
            image_path.unlink()
    except Exception:
        pass


def _detect_image_format(image_bytes: bytes) -> str:
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            image_format = (image.format or "JPEG").lower()
    except Exception:
        image_format = "jpeg"
    if image_format == "jpg":
        image_format = "jpeg"
    return image_format


def ingest_and_run_agentic(
    *,
    image_bytes: bytes,
    context: str | None,
    context_source: str | None,
    db: Session,
    source_channel: str,
    image_id: UUID | str | None = None,
    content_type: str | None = None,
    source_url: str | None = None,
) -> AgentRunResponse:
    if image_id is None:
        resolved_image_id = uuid4()
    else:
        try:
            resolved_image_id = UUID(str(image_id))
        except ValueError as exc:
            raise HTTPException(
                status_code=400, detail="Invalid image_id format."
            ) from exc
    image_hash = hashlib.sha256(image_bytes).hexdigest()
    detected_format = imghdr.what(None, h=image_bytes)
    if not detected_format:
        logger.error(
            "Unable to detect image format for upload. image_hash=%s",
            image_hash,
        )
        raise HTTPException(
            status_code=400, detail="Unsupported or invalid image file."
        )

    image_format = detected_format.lower()
    if image_format == "jpg":
        image_format = "jpeg"

    detected_mime_type = f"image/{image_format}"
    mime_type = detected_mime_type
    if content_type:
        if content_type != detected_mime_type:
            logger.warning(
                "Content type mismatch for upload. image_hash=%s detected=%s provided=%s",
                image_hash,
                detected_mime_type,
                content_type,
            )
        else:
            mime_type = detected_mime_type

    stored_image_path = _persist_image_bytes(
        image_id=resolved_image_id,
        image_bytes=image_bytes,
        image_format=image_format,
    )

    agent = MedContextLangGraphAgent()
    try:
        with db.begin():
            # Check if image already exists by hash
            existing_submission = (
                db.query(ImageSubmission)
                .filter(ImageSubmission.image_hash == image_hash)
                .first()
            )

            if existing_submission:
                # Reuse existing submission
                submission = existing_submission
                resolved_image_id = existing_submission.id
            else:
                # Create new submission
                submission = ImageSubmission(
                    id=resolved_image_id,
                    source_channel=source_channel,
                    user_id=None,
                    image_hash=image_hash,
                    image_path=str(stored_image_path),
                    file_size=len(image_bytes),
                    mime_type=mime_type,
                    image_format=image_format,
                    width=None,
                    height=None,
                    orientation_corrected=False,
                    metadata_extracted=False,
                )
                try:
                    db.add(submission)
                    db.flush()
                except IntegrityError:
                    db.rollback()
                    # Race condition: another request inserted the same hash
                    existing_submission = (
                        db.query(ImageSubmission)
                        .filter(ImageSubmission.image_hash == image_hash)
                        .first()
                    )
                    if existing_submission is None:
                        raise HTTPException(
                            status_code=500,
                            detail="Failed to create or retrieve image submission.",
                        )
                    submission = existing_submission
                    resolved_image_id = existing_submission.id

            submission_context = SubmissionContext(
                image_id=resolved_image_id,
                surrounding_text=context,
                claimed_condition=None,
                claimed_origin=None,
                source_url=source_url,
                source_whatsapp_group=None,
                language_code="en",
            )
            db.add(submission_context)
            store_provenance_manifest(
                db,
                image_hash=image_hash,
                image_id=resolved_image_id,
                source_url=source_url,
            )
            result = agent.run(
                image_bytes=image_bytes,
                image_id=str(resolved_image_id),
                context=context,
            )

            triage_payload = result.triage
            triage_json = json.dumps(triage_payload, default=str, ensure_ascii=True)
            clinical_impression = None
            if isinstance(triage_payload, dict):
                clinical_impression = triage_payload.get("primary_findings")
            analysis = MedGemmaAnalysis(
                image_id=resolved_image_id,
                key_findings=triage_json,
                clinical_impression=clinical_impression,
                claimed_condition_analyzed=bool(context),
                model_version=settings.medgemma_hf_model,
            )
            db.add(analysis)
    except Exception:
        _cleanup_image_file(stored_image_path)
        raise

    return AgentRunResponse(
        triage=result.triage,
        tool_results=result.tool_results,
        synthesis=result.synthesis,
        context_used=context,
        context_source=context_source,
    )


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
    image_bytes = await file.read()
    return ingest_and_run_agentic(
        image_bytes=image_bytes,
        context=context,
        context_source="user",
        db=db,
        source_channel="agentic",
        content_type=file.content_type,
    )
