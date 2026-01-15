from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrityWeights:
    plausibility: float = 0.4
    genealogy_consistency: float = 0.3
    source_reputation: float = 0.3


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_integrity_score(
    *,
    plausibility: float | None,
    genealogy_consistency: float | None,
    source_reputation: float | None,
    weights: IntegrityWeights | None = None,
) -> float:
    """Compute the MedContext Integrity Score (0.0-1.0).

    The score is a weighted average of three signals:
    - plausibility (MedGemma)
    - genealogy consistency (provenance/blockchain)
    - source reputation (reverse search)
    """

    active_weights = weights or IntegrityWeights()
    weighted_values: list[tuple[float, float]] = [
        (active_weights.plausibility, plausibility),
        (active_weights.genealogy_consistency, genealogy_consistency),
        (active_weights.source_reputation, source_reputation),
    ]

    total_weight = 0.0
    score = 0.0
    for weight, value in weighted_values:
        if value is None:
            continue
        total_weight += weight
        score += weight * _clamp(float(value))

    if total_weight == 0:
        return 0.0

    return _clamp(score / total_weight)
