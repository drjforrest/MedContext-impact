from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.clinical.medgemma_client import MedGemmaClientError
from app.orchestrator.agent import MedContextAgent
from app.orchestrator.langgraph_agent import MedContextLangGraphAgent
from app.schemas.orchestrator import AgentRunResponse
from app.schemas.trace import TraceResponse

router = APIRouter()


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    file: UploadFile = File(...),
    image_id: str | None = Form(default=None),
) -> AgentRunResponse:
    image_bytes = await file.read()
    agent = MedContextAgent()
    try:
        result = agent.run(image_bytes=image_bytes, image_id=image_id)
    except MedGemmaClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AgentRunResponse(
        triage=result.triage,
        tool_results=result.tool_results,
        synthesis=result.synthesis,
    )


@router.post("/run-langgraph", response_model=AgentRunResponse)
async def run_agent_langgraph(
    file: UploadFile = File(...),
    image_id: str | None = Form(default=None),
) -> AgentRunResponse:
    image_bytes = await file.read()
    agent = MedContextLangGraphAgent()
    try:
        result = agent.run(image_bytes=image_bytes, image_id=image_id)
    except MedGemmaClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AgentRunResponse(
        triage=result.triage,
        tool_results=result.tool_results,
        synthesis=result.synthesis,
    )


@router.get("/graph", response_model=str)
async def get_langgraph_mermaid() -> str:
    agent = MedContextLangGraphAgent()
    return agent.get_graph_mermaid()


@router.post("/trace", response_model=TraceResponse)
async def run_agent_trace(
    file: UploadFile = File(...),
    image_id: str | None = Form(default=None),
) -> TraceResponse:
    image_bytes = await file.read()
    agent = MedContextLangGraphAgent()
    try:
        state = agent.run_with_trace(image_bytes=image_bytes, image_id=image_id)
    except MedGemmaClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    trace_entries = state.get("trace", [])
    total_duration_ms = sum(
        entry.get("duration_ms", 0)
        for entry in trace_entries
        if isinstance(entry, dict)
    )

    return TraceResponse(
        trace_id=state.get("trace_id"),
        triage=state.get("triage"),
        tool_results=state.get("tool_results", {}),
        synthesis=state.get("synthesis"),
        total_duration_ms=total_duration_ms,
        trace=trace_entries,
    )
