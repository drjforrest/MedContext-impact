from typing import Any

from pydantic import AnyHttpUrl, BaseModel


class ResolveUrlRequest(BaseModel):
    image_url: AnyHttpUrl


class ResolvedUrlResponse(BaseModel):
    image_url: str
    images: list[str]
    context: str | None = None


class AgentRunResponse(BaseModel):
    triage: Any
    tool_results: dict[str, Any]
    synthesis: Any
    context_used: str | None = None
    context_source: str | None = None


class MedGemmaModelAvailability(BaseModel):
    id: str
    name: str
    model: str
    description: str
    provider: str
    available: bool
