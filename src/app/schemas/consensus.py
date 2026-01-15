from __future__ import annotations

from typing import Dict, List, Optional

from pydantic import BaseModel


class ConsensusClaim(BaseModel):
    claim_text: str
    verdict: Optional[str] = None
    confidence_this_is_claim: Optional[float] = None
    matches_medgemma: Optional[bool] = None
    source_type: Optional[str] = None
    is_deepfake: Optional[bool] = None


class ConsensusRequest(BaseModel):
    image_id: Optional[str] = None
    claims: List[ConsensusClaim]


class ConsensusDistributionEntry(BaseModel):
    count: int
    percentage: float
    examples: List[str]


class ConsensusResponse(BaseModel):
    image_id: Optional[str] = None
    total_instances_found: int
    distribution: Dict[str, ConsensusDistributionEntry]
    consensus: str
    confidence_in_consensus: float
