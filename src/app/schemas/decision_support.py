from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class DecisionSupportRequest(BaseModel):
    image_id: Optional[str] = None
    audience: str
    consensus: Optional[str] = None
    integrity_score: Optional[float] = None
    key_findings: Optional[List[str]] = None


class DecisionSupportResponse(BaseModel):
    audience: str
    headline: str
    summary: str
    recommended_action: str
    evidence: List[str]
    red_flags: List[str]
    next_steps: List[str]
