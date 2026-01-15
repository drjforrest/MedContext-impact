from typing import Any

from pydantic import BaseModel


class AgentRunResponse(BaseModel):
    triage: Any
    tool_results: dict[str, Any]
    synthesis: Any
