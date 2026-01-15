from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ClaimTypeScore(BaseModel):
    type: str
    confidence: float


class ClaimItem(BaseModel):
    claim_id: str
    claim_text: str
    sentence_index: int
    claim_types: List[ClaimTypeScore]
    flags: List[str]
    confidence_this_is_claim: float


class ClaimExtractionRequest(BaseModel):
    text: str
    image_id: Optional[str] = None
    language: Optional[str] = None


class ClaimExtractionResponse(BaseModel):
    image_id: Optional[str] = None
    language: str
    total_sentences: int
    claims_extracted: int
    claims: List[ClaimItem]


class ClaimClusterRequest(BaseModel):
    claims: List[ClaimItem]


class ClaimFamily(BaseModel):
    family_id: int
    size: int
    representative_claim: str
    variant_count: int
    variants: List[str]
    claim_types: List[str]
    health_severity: str


class ClaimClusterResponse(BaseModel):
    total_claims: int
    families_identified: int
    families: List[ClaimFamily]
