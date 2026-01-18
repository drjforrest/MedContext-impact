from uuid import uuid4

from fastapi import APIRouter, File, Form, UploadFile

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
) -> AgentRunResponse:
    image_id = uuid4()
    image_bytes = await file.read()
    agent = MedContextAgent()
    result = agent.run(image_bytes=image_bytes, image_id=str(image_id))
    return AgentRunResponse(
        triage={"context": context, "triage": result.triage},
        tool_results=result.tool_results,
        synthesis=result.synthesis,
    )
