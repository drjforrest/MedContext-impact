from __future__ import annotations

from app.schemas.decision_support import DecisionSupportRequest, DecisionSupportResponse


def build_decision_support(payload: DecisionSupportRequest) -> DecisionSupportResponse:
    audience = (payload.audience or "public").lower()
    consensus = payload.consensus or "unknown"
    integrity_score = payload.integrity_score
    integrity_label = _integrity_label(integrity_score)

    headline = _headline_for_audience(audience, consensus, integrity_label)
    summary = _summary_for_audience(audience, consensus, integrity_label)
    recommended_action = _action_for_integrity(integrity_label)
    evidence = (
        payload.key_findings
        if payload.key_findings is not None
        else _default_evidence(consensus)
    )
    red_flags = _default_red_flags(consensus)
    next_steps = _default_next_steps(audience)

    return DecisionSupportResponse(
        audience=audience,
        headline=headline,
        summary=summary,
        recommended_action=recommended_action,
        evidence=evidence,
        red_flags=red_flags,
        next_steps=next_steps,
    )


def _integrity_label(score: float | None) -> str:
    if score is None:
        return "unknown"
    if score > 0.8:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _headline_for_audience(audience: str, consensus: str, integrity_label: str) -> str:
    if audience == "clinician":
        return (
            f"Clinical Brief: {consensus.replace('_', ' ').title()} ({integrity_label})"
        )
    if audience == "journalist":
        return f"Story Lead: Image usage is {consensus.replace('_', ' ')}"
    if audience == "public":
        return "What this image really shows"
    return f"Decision Support Summary ({integrity_label})"


def _summary_for_audience(audience: str, consensus: str, integrity_label: str) -> str:
    base = (
        f"Consensus indicates {consensus.replace('_', ' ')} with "
        f"{integrity_label} integrity."
    )
    if audience == "clinician":
        return f"{base} Use clinical guidance and confirm with patient context."
    if audience == "journalist":
        return f"{base} Focus on provenance and fact-check alignment."
    if audience == "public":
        return f"{base} Verify sources before sharing."
    return base


def _action_for_integrity(integrity_label: str) -> str:
    if integrity_label == "high":
        return "Proceed with standard guidance."
    if integrity_label == "medium":
        return "Review supporting evidence before acting."
    if integrity_label == "low":
        return "Escalate for expert review."
    return "Insufficient data; gather more evidence."


def _default_evidence(consensus: str) -> list[str]:
    consensus_lower = consensus.lower()
    if "misinformation" in consensus_lower:
        return ["Fact-check alignment indicates false or misleading usage."]
    if "legitimate" in consensus_lower:
        return ["Usage aligns with MedGemma findings and clinical sources."]
    return ["Evidence mixed; additional verification recommended."]


def _default_red_flags(consensus: str) -> list[str]:
    flags = ["Lack of primary source attribution"]
    consensus_lower = consensus.lower()
    if "misinformation" in consensus_lower or "concerns" in consensus_lower:
        flags.append("Narratives conflict with medical consensus")
    if "unclear" in consensus_lower:
        flags.append("Context is ambiguous or incomplete")
    return flags


def _default_next_steps(audience: str) -> list[str]:
    if audience == "clinician":
        return [
            "Discuss uncertainties with the patient",
            "Reference clinical guidelines or expert sources",
        ]
    if audience == "journalist":
        return [
            "Contact medical experts for confirmation",
            "Cite primary sources and fact-checks",
        ]
    if audience == "public":
        return ["Check reputable health sources", "Avoid resharing unverified claims"]
    return ["Gather more data and rerun analysis"]
    return ["Gather more data and rerun analysis"]
    return ["Gather more data and rerun analysis"]
