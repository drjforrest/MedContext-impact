from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List

from app.schemas.claims import (
    ClaimClusterRequest,
    ClaimClusterResponse,
    ClaimExtractionRequest,
    ClaimExtractionResponse,
    ClaimFamily,
    ClaimItem,
    ClaimTypeScore,
)


_URL_RE = re.compile(r"http\S+|www\S+", re.IGNORECASE)
_SENTENCE_SPLIT_RE = re.compile(r"[.!?]+\s+")


_CLAIM_TYPE_KEYWORDS = {
    "vaccine_injury_claim": ["vaccine", "injury", "side effect", "damage"],
    "treatment_efficacy_claim": ["cure", "treatment", "healed", "miracle"],
    "misdiagnosis_claim": ["misdiagnosis", "wrong diagnosis", "misdiagnosed"],
    "disease_severity_exaggeration": ["deadly", "kills", "fatal", "destroy"],
    "attribution_error": ["not from", "fake patient", "wrong person"],
    "deepfake_or_manipulated_image": ["deepfake", "manipulated", "edited", "fake image"],
    "medical_misinformation": ["hoax", "cover-up", "truth hidden"],
}

_MEDICAL_TERMS = {
    "x-ray",
    "mri",
    "ct",
    "ultrasound",
    "pneumonia",
    "tumor",
    "cancer",
    "fracture",
    "lesion",
    "infection",
    "vaccine",
    "cardiac",
    "lung",
    "brain",
}


def extract_claims(payload: ClaimExtractionRequest) -> ClaimExtractionResponse:
    text = _normalize_text(payload.text)
    sentences = _split_sentences(text)
    claims: List[ClaimItem] = []
    for idx, sentence in enumerate(sentences):
        sentence_clean = sentence.strip()
        if not sentence_clean:
            continue
        claim_types = _classify_claim_types(sentence_clean)
        flags = _generate_flags(sentence_clean)
        confidence = _estimate_claim_confidence(sentence_clean, claim_types, flags)
        if confidence < 0.25:
            continue
        claim_id = f"CLM_{payload.image_id or 'img'}_{idx:03d}"
        claims.append(
            ClaimItem(
                claim_id=claim_id,
                claim_text=sentence_clean,
                sentence_index=idx,
                claim_types=claim_types,
                flags=flags,
                confidence_this_is_claim=confidence,
            )
        )
    return ClaimExtractionResponse(
        image_id=payload.image_id,
        language=payload.language or "en",
        total_sentences=len(sentences),
        claims_extracted=len(claims),
        claims=claims,
    )


def cluster_claims(payload: ClaimClusterRequest) -> ClaimClusterResponse:
    clusters: List[list[ClaimItem]] = []
    representatives: List[str] = []
    for claim in payload.claims:
        claim_tokens = _tokenize(claim.claim_text)
        assigned = False
        for idx, rep_text in enumerate(representatives):
            similarity = _jaccard_similarity(claim_tokens, _tokenize(rep_text))
            if similarity >= 0.35:
                clusters[idx].append(claim)
                assigned = True
                break
        if not assigned:
            clusters.append([claim])
            representatives.append(claim.claim_text)
    families: List[ClaimFamily] = []
    for idx, cluster in enumerate(clusters, start=1):
        representative = cluster[0]
        variants = [c.claim_text for c in cluster[1:]]
        claim_types = sorted(
            {ct.type for c in cluster for ct in c.claim_types}
        )
        families.append(
            ClaimFamily(
                family_id=idx,
                size=len(cluster),
                representative_claim=representative.claim_text,
                variant_count=len(variants),
                variants=variants,
                claim_types=claim_types,
                health_severity=_assess_severity(claim_types),
            )
        )
    return ClaimClusterResponse(
        total_claims=len(payload.claims),
        families_identified=len(families),
        families=families,
    )


def _normalize_text(text: str) -> str:
    cleaned = _URL_RE.sub("[URL]", text)
    cleaned = " ".join(cleaned.split())
    return cleaned


def _split_sentences(text: str) -> list[str]:
    if not text:
        return []
    return _SENTENCE_SPLIT_RE.split(text)


def _classify_claim_types(sentence: str) -> list[ClaimTypeScore]:
    lowered = sentence.lower()
    scored: list[ClaimTypeScore] = []
    for claim_type, keywords in _CLAIM_TYPE_KEYWORDS.items():
        matches = sum(1 for kw in keywords if kw in lowered)
        if matches:
            score = min(1.0, 0.3 + 0.2 * matches)
            scored.append(ClaimTypeScore(type=claim_type, confidence=score))
    if not scored and any(term in lowered for term in _MEDICAL_TERMS):
        scored.append(ClaimTypeScore(type="medical_claim", confidence=0.4))
    return scored


def _generate_flags(sentence: str) -> list[str]:
    flags = []
    lowered = sentence.lower()
    if any(marker in lowered for marker in ["i heard", "someone told me", "my friend"]):
        flags.append("anecdotal_evidence_presented_as_fact")
    if any(marker in lowered for marker in ["caused by", "leads to", "resulted in"]):
        flags.append("causal_claim_without_evidence")
    if any(word in lowered for word in ["deadly", "kills", "destroy", "poison"]):
        flags.append("emotionally_charged_language")
    if "[url]" in lowered:
        flags.append("external_link_present")
    return flags


def _estimate_claim_confidence(
    sentence: str, claim_types: Iterable[ClaimTypeScore], flags: list[str]
) -> float:
    base = 0.2
    if any(term in sentence.lower() for term in _MEDICAL_TERMS):
        base += 0.2
    base += 0.1 * len(list(claim_types))
    if "anecdotal_evidence_presented_as_fact" in flags:
        base -= 0.1
    return max(0.0, min(1.0, base))


def _tokenize(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    return {t for t in tokens if len(t) > 2}


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = a & b
    union = a | b
    return len(intersection) / len(union)


def _assess_severity(claim_types: Iterable[str]) -> str:
    severity_map = {
        "vaccine_injury_claim": "HIGH",
        "treatment_efficacy_claim": "HIGH",
        "deepfake_or_manipulated_image": "HIGH",
        "misdiagnosis_claim": "MEDIUM",
        "disease_severity_exaggeration": "MEDIUM",
        "medical_misinformation": "MEDIUM",
        "attribution_error": "LOW",
        "medical_claim": "LOW",
    }
    highest = "LOW"
    for claim_type in claim_types:
        level = severity_map.get(claim_type, "LOW")
        if level == "HIGH":
            return "HIGH"
        if level == "MEDIUM":
            highest = "MEDIUM"
    return highest
