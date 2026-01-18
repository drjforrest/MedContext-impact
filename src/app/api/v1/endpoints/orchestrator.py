import asyncio
import ipaddress
import socket
from urllib.parse import urlparse

import httpx
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.clinical.medgemma_client import MedGemmaClientError
from app.orchestrator.agent import MedContextAgent
from app.orchestrator.image_scrape import extract_image_candidates, extract_page_context
from app.orchestrator.langgraph_agent import MedContextLangGraphAgent
from app.schemas.orchestrator import (
    AgentRunResponse,
    ResolvedUrlResponse,
    ResolveUrlRequest,
)
from app.schemas.trace import TraceResponse

router = APIRouter()


def _is_disallowed_ip(ip: ipaddress._BaseAddress) -> bool:
    if str(ip) == "169.254.169.254":
        return True
    return (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_reserved
        or ip.is_multicast
        or ip.is_unspecified
    )


async def _resolve_and_validate_ips(hostname: str) -> list[str]:
    normalized = hostname.strip().lower().rstrip(".")
    if not normalized:
        raise ValueError("Missing hostname.")

    try:
        ip = ipaddress.ip_address(normalized)
    except ValueError:
        pass
    else:
        if _is_disallowed_ip(ip):
            raise ValueError("Disallowed IP address.")
        return [str(ip)]

    try:
        addr_info = await asyncio.get_running_loop().getaddrinfo(
            normalized, None, family=socket.AF_UNSPEC, type=socket.SOCK_STREAM
        )
    except OSError as exc:
        raise ValueError("Failed to resolve hostname.") from exc

    if not addr_info:
        raise ValueError("Hostname did not resolve.")

    resolved_ips: list[str] = []
    seen: set[str] = set()
    for _, _, _, _, sockaddr in addr_info:
        resolved_ip = sockaddr[0]
        try:
            ip = ipaddress.ip_address(resolved_ip)
        except ValueError as exc:
            raise ValueError("Invalid resolved IP address.") from exc
        if _is_disallowed_ip(ip):
            raise ValueError("Resolved IP address is disallowed.")
        ip_text = str(ip)
        if ip_text not in seen:
            seen.add(ip_text)
            resolved_ips.append(ip_text)

    if not resolved_ips:
        raise ValueError("Hostname did not resolve.")
    return resolved_ips


async def _is_safe_url(image_url: str) -> bool:
    try:
        parsed = urlparse(image_url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    hostname = parsed.hostname
    if not hostname:
        return False

    normalized = hostname.strip().lower().rstrip(".")
    if normalized in {"localhost", "localhost.localdomain", "0.0.0.0"}:
        return False
    if normalized in {"metadata.google.internal", "metadata"}:
        return False
    try:
        await _resolve_and_validate_ips(normalized)
    except ValueError:
        return False
    return True


async def _require_public_http_url(image_url: str) -> None:
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url is required.")
    if not await _is_safe_url(image_url):
        raise HTTPException(
            status_code=400, detail="image_url must be a public http(s) URL."
        )
    parsed = urlparse(image_url)
    if parsed.scheme not in {"http", "https"}:
        raise HTTPException(status_code=400, detail="image_url must be http or https.")


def _resolve_context(
    context: str | None, scraped_context: str | None
) -> tuple[str | None, str | None]:
    context_used = scraped_context if context is None else context
    context_source = None
    if context is not None:
        context_source = "user"
    elif scraped_context:
        context_source = "scraped"
    return context_used, context_source


async def _get_with_ssrf_checks(
    client: httpx.AsyncClient, url: str, *, max_redirects: int = 5
) -> httpx.Response:
    await _require_public_http_url(url)
    current_url = url
    for _ in range(max_redirects):
        response = await _send_pinned_request(client, current_url)
        if response.is_redirect:
            await response.aclose()
            location = response.headers.get("location")
            if not location:
                raise HTTPException(
                    status_code=400,
                    detail="image_url redirect missing location header.",
                )
            next_url = httpx.URL(current_url).join(location)
            next_url_str = str(next_url)
            await _require_public_http_url(next_url_str)
            current_url = next_url_str
            continue
        return response
    raise HTTPException(status_code=400, detail="image_url redirected too many times.")


async def _send_pinned_request(client: httpx.AsyncClient, url: str) -> httpx.Response:
    parsed = httpx.URL(url)
    hostname = parsed.host
    if not hostname:
        raise HTTPException(
            status_code=400, detail="image_url must include a hostname."
        )

    try:
        resolved_ips = await _resolve_and_validate_ips(hostname)
    except ValueError as exc:
        raise HTTPException(
            status_code=400, detail="image_url must be a public http(s) URL."
        ) from exc

    last_error: httpx.HTTPError | None = None
    for resolved_ip in resolved_ips:
        pinned_url = parsed.copy_with(host=resolved_ip)
        request = client.build_request("GET", pinned_url, headers={"Host": hostname})
        request.extensions["sni_hostname"] = hostname
        request.extensions["server_hostname"] = hostname
        try:
            return await client.send(request)
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            last_error = exc
            continue

    if last_error is not None:
        raise last_error
    raise HTTPException(
        status_code=400, detail="image_url did not resolve to a reachable host."
    )


@router.post("/resolve-url", response_model=ResolvedUrlResponse)
async def resolve_url(payload: ResolveUrlRequest) -> ResolvedUrlResponse:
    image_url = payload.image_url.strip()
    await _require_public_http_url(image_url)
    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "MedContext/1.0 (+https://medcontext.local)"},
        ) as client:
            response = await _get_with_ssrf_checks(client, image_url)
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
    await _require_public_http_url(image_url)
    try:
        async with httpx.AsyncClient(
            timeout=20.0,
            follow_redirects=False,
            trust_env=False,
            headers={"User-Agent": "MedContext/1.0 (+https://medcontext.local)"},
        ) as client:
            response = await _get_with_ssrf_checks(client, image_url)
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
                await _require_public_http_url(image_link)
                image_response = await _get_with_ssrf_checks(client, image_link)
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
    if file is not None and image_url:
        raise HTTPException(
            status_code=400, detail="Provide exactly one of file or image_url."
        )
    if file is not None:
        return await file.read(), None
    if image_url:
        return await _fetch_image_bytes(image_url)
    raise HTTPException(status_code=400, detail="Provide an image file or image_url.")


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(
    file: UploadFile | None = File(default=None),
    image_url: str | None = Form(default=None),
    context: str | None = Form(default=None),
    image_id: str | None = Form(default=None),
) -> AgentRunResponse:
    image_bytes, scraped_context = await _resolve_image_input(file, image_url)
    context_used, context_source = _resolve_context(context, scraped_context)
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
    context_used, context_source = _resolve_context(context, scraped_context)
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
    context_used, _ = _resolve_context(context, scraped_context)
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
