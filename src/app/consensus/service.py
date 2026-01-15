from __future__ import annotations

from typing import Dict, List

from app.schemas.consensus import (
    ConsensusDistributionEntry,
    ConsensusRequest,
    ConsensusResponse,
)

_LEGITIMATE_CATEGORIES = {"medical_educational", "clinical_legitimate"}


def calculate_consensus(payload: ConsensusRequest) -> ConsensusResponse:
    total_instances = len(payload.claims)
    categorized: Dict[str, List[str]] = {
        "medical_educational": [],
        "clinical_legitimate": [],
        "unclear_context": [],
        "misleading": [],
        "false": [],
        "deepfake": [],
        "unverifiable": [],
    }

    for claim in payload.claims:
        category = _categorize_claim(claim)
        categorized[category].append(claim.claim_text)

    distribution = {
        category: ConsensusDistributionEntry(
            count=len(claims),
            percentage=round(len(claims) / total_instances * 100, 1)
            if total_instances
            else 0.0,
            examples=[text[:80] for text in claims[:3]],
        )
        for category, claims in categorized.items()
        if claims
    }

    consensus = _determine_consensus(distribution)
    confidence = _calculate_confidence(total_instances)

    return ConsensusResponse(
        image_id=payload.image_id,
        total_instances_found=total_instances,
        distribution=distribution,
        consensus=consensus,
        confidence_in_consensus=confidence,
    )


def _categorize_claim(claim) -> str:
    verdict = (claim.verdict or "").lower()
    if claim.is_deepfake:
        return "deepfake"
    if verdict in {"false", "misinformation"}:
        return "false"
    if verdict in {"unverifiable", "unknown"}:
        return "unverifiable"
    confidence = claim.confidence_this_is_claim
    if confidence is not None and confidence < 0.3:
        return "unclear_context"
    if claim.matches_medgemma is True:
        if claim.source_type in {"medical_journal", "clinical_document"}:
            return "clinical_legitimate"
        return "medical_educational"
    if claim.matches_medgemma is False:
        return "misleading"
    return "unclear_context"


def _determine_consensus(distribution: Dict[str, ConsensusDistributionEntry]) -> str:
    if not distribution:
        return "unknown"
    sorted_categories = sorted(distribution.items(), key=lambda x: (-x[1].count, x[0]))
    dominant_category = sorted_categories[0][0]
    dominant_percentage = sorted_categories[0][1].percentage
    if dominant_category in _LEGITIMATE_CATEGORIES:
        return (
            "legitimate_use_dominant"
            if dominant_percentage >= 50
            else "mixed_usage_with_legitimate_primary"
        )
    if dominant_category == "deepfake":
        return (
            "primarily_used_for_deepfakes"
            if dominant_percentage >= 50
            else "mixed_usage_with_deepfake_primary"
        )
    if dominant_category == "false":
        return "primarily_used_for_misinformation"
    if dominant_category == "unclear_context":
        return "usage_context_unclear"
    return "mixed_usage_with_concerns"


def _calculate_confidence(total_instances: int) -> float:
    if total_instances < 10:
        return 0.3
    if total_instances < 100:
        return 0.6
    return 0.9
