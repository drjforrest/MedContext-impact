from typing import Any

from pydantic import BaseModel


class TraceEntry(BaseModel):
    trace_id: str
    node: str
    timestamp: str
    duration_ms: int
    data: dict[str, Any]


class TraceResponse(BaseModel):
    trace_id: str
    triage: Any
    tool_results: dict[str, Any]
    synthesis: Any
    total_duration_ms: int
    trace: list[TraceEntry]
