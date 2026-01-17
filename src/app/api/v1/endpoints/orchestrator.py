from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.orchestrator.image_scrape import extract_image_candidates, extract_page_context

from app.clinical.medgemma_client import MedGemmaClientError
from app.orchestrator.agent import MedContextAgent
from app.orchestrator.langgraph_agent import MedContextLangGraphAgent
from app.schemas.orchestrator import (
    AgentRunResponse,
    ResolveUrlRequest,
    ResolvedUrlResponse,
)
from app.schemas.trace import TraceResponse

router = APIRouter()


@router.post("/resolve-url", response_model=ResolvedUrlResponse)
async def resolve_url(payload: ResolveUrlRequest) -> ResolvedUrlResponse:
    image_url = payload.image_url.strip()
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=400, detail="image_url must be http or https."
        )
    try:
        async with httpx.AsyncClient(
            timeout=20.0, follow_redirects=True
        ) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if content_type.startswith("image/"):
                return ResolvedUrlResponse(
                    image_url=image_url, images=[image_url], context=None
                )
            html = response.text
            candidates = extract_image_candidates(html, image_url)
            context = extract_page_context(html, image_url)
            return ResolvedUrlResponse(
                image_url=image_url, images=candidates, context=context
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to resolve image_url: {exc}"
        ) from exc


async def _fetch_image_bytes(image_url: str) -> tuple[bytes, str | None]:
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required.")
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(
            status_code=400, detail="image_url must be http or https."
        )
    try:
        async with httpx.AsyncClient(
            timeout=20.0, follow_redirects=True
        ) as client:
            response = await client.get(image_url)
            response.raise_for_status()
            content_type = response.headers.get("content-type", "").lower()
            if content_type.startswith("image/"):
                return response.content, None
            if "text/html" in content_type or not content_type:
                html = response.text
                candidates = extract_image_candidates(html, image_url)
                if not candidates:
                    raise HTTPException(
                        status_code=400,
                        detail="No image found at URL. Provide a direct image URL.",
                    )
                if len(candidates) > 1:
                    sample = ", ".join(candidates[:3])
                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Multiple images found at URL. Provide a direct image URL. "
                            f"Examples: {sample}"
                        ),
                    )
                image_link = candidates[0]
                image_response = await client.get(image_link)
                image_response.raise_for_status()
                image_type = image_response.headers.get("content-type", "").lower()
                if not image_type.startswith("image/"):
                    raise HTTPException(
                        status_code=400,
                        detail="Resolved image URL does not point to an image.",
                    )
                return image_response.content, extract_page_context(html, image_url)
            raise HTTPException(
                status_code=400,
                detail="image_url did not return image content.",
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=400, detail=f"Failed to fetch image_url: {exc}"
        ) from exc


async def _resolve_image_input(
    file: UploadFile | None, image_url: str | None
) -> tuple[bytes, str | None]:
    if file is not None:
        return await file.read(), None
    if image_url:
        return await _fetch_image_bytes(image_url)
    raise HTTPException(
        status_code=400, detail="Provide an image file or image_url."
    )


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    file: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    context: str | None = Form(default=None),
    image_id: str | None = Form(default=None),
) -> AgentRunResponse:
    image_bytes, scraped_context = await _resolve_image_input(file, image_url)
    context_used = context or scraped_context
    context_source = None
    if context_used:
        context_source = "user" if context else "scraped"
    agent = MedContextAgent()
    try:
        result = agent.run(
            image_bytes=image_bytes, image_id=image_id, context=context_used
        )
    except MedGemmaClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AgentRunResponse(
        triage=result.triage,
        tool_results=result.tool_results,
        synthesis=result.synthesis,
        context_used=context_used,
        context_source=context_source,
    )


@router.post("/run-langgraph", response_model=AgentRunResponse)
async def run_agent_langgraph(
    file: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    context: str | None = Form(default=None),
    image_id: str | None = Form(default=None),
) -> AgentRunResponse:
    image_bytes, scraped_context = await _resolve_image_input(file, image_url)
    context_used = context or scraped_context
    context_source = None
    if context_used:
        context_source = "user" if context else "scraped"
    agent = MedContextLangGraphAgent()
    try:
        result = agent.run(
            image_bytes=image_bytes, image_id=image_id, context=context_used
        )
    except MedGemmaClientError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return AgentRunResponse(
        triage=result.triage,
        tool_results=result.tool_results,
        synthesis=result.synthesis,
        context_used=context_used,
        context_source=context_source,
    )


@router.get("/graph", response_model=str)
async def get_langgraph_mermaid() -> str:
    agent = MedContextLangGraphAgent()
    return agent.get_graph_mermaid()


@router.post("/trace", response_model=TraceResponse)
async def run_agent_trace(
    file: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    context: str | None = Form(default=None),
    image_id: str | None = Form(default=None),
) -> TraceResponse:
    image_bytes, scraped_context = await _resolve_image_input(file, image_url)
    context_used = context or scraped_context
    agent = MedContextLangGraphAgent()
    try:
        state = agent.run_with_trace(
            image_bytes=image_bytes, image_id=image_id, context=context_used
        )
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
