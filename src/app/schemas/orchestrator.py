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
    is_misinformation: bool | None = None
    context_used: str | None = None
    context_source: str | None = None


class MedGemmaModelAvailability(BaseModel):
    id: str
    name: str
    model: str
    description: str
    provider: str
    available: bool
    recommended_veracity_threshold: float = 0.65
    recommended_alignment_threshold: float = 0.30
    recommended_decision_logic: str = "OR"
