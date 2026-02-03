from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class IntegrityWeights:
    plausibility: float = 0.4
    genealogy_consistency: float = 0.3
    source_reputation: float = 0.3


@dataclass(frozen=True)
class ContextualIntegrityWeights:
    alignment: float = 0.6
    plausibility: float = 0.15
    genealogy_consistency: float = 0.15
    source_reputation: float = 0.1


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _compute_weighted_score(values: list[tuple[float, float | None]]) -> float:
    """Compute weighted score with dynamic weight redistribution.

    Missing signals (None) have their weights redistributed proportionally
    to available signals. This ensures the score reflects the quality of
    available evidence rather than penalizing for missing data.

    Example: With weights 60/15/15/10, if Genealogy and Source are None:
    - Total available weight = 60 + 15 = 75%
    - Alignment gets: 60/75 = 80% of final score
    - Plausibility gets: 15/75 = 20% of final score
    - Result: Final score = (0.6/0.75)×alignment + (0.15/0.75)×plausibility
    """
    # Separate available and missing signals
    available = [(w, v) for w, v in values if v is not None]

    if not available:
        return 0.0

    # Calculate total weight of available signals
    total_available_weight = sum(w for w, _ in available)

    if total_available_weight <= 0:
        return 0.0

    # Compute score with redistributed weights
    score = 0.0
    for weight, value in available:
        # Redistribute: this signal's share of available weight
        redistributed_weight = weight / total_available_weight
        signal_value = _clamp(float(value))
        score += redistributed_weight * signal_value

    return _clamp(score)


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
    weighted_values: list[tuple[float, float | None]] = [
        (active_weights.plausibility, plausibility),
        (active_weights.genealogy_consistency, genealogy_consistency),
        (active_weights.source_reputation, source_reputation),
    ]
    return _compute_weighted_score(weighted_values)


def compute_contextual_integrity_score(
    *,
    alignment: float | None,
    plausibility: float | None,
    genealogy_consistency: float | None,
    source_reputation: float | None,
    weights: ContextualIntegrityWeights | None = None,
) -> float:
    """Compute contextual authenticity score with alignment as primary signal."""
    active_weights = weights or ContextualIntegrityWeights()
    weighted_values: list[tuple[float, float | None]] = [
        (active_weights.alignment, alignment),
        (active_weights.plausibility, plausibility),
        (active_weights.genealogy_consistency, genealogy_consistency),
        (active_weights.source_reputation, source_reputation),
    ]
    return _compute_weighted_score(weighted_values)
