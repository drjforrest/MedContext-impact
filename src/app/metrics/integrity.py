from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ContextualIntegrityWeights:
    alignment: float = 0.6
    plausibility: float = 0.15
    genealogy_consistency: float = 0.15
    source_reputation: float = 0.1


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _compute_weighted_score(values: list[tuple[float, float | None]]) -> float:
    """Compute weighted score treating None values as 0.0.

    Missing signals (None) are treated as 0.0 without redistributing weights.
    Each signal contributes its weight multiplied by its clamped value.
    """
    # Iterate over the original values list, treating None as 0.0
    score = 0.0
    for weight, value in values:
        signal_value = 0.0 if value is None else _clamp(float(value))
        score += weight * signal_value

    return _clamp(score)


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
