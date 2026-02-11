"""Tests for the MedContext Contextual Integrity Score calculation."""

import pytest

from app.metrics.integrity import (
    ContextualIntegrityWeights,
    compute_contextual_integrity_score,
)


class TestContextualIntegrityScore:
    """Test suite for contextual integrity score computation."""

    @pytest.mark.unit
    def test_compute_perfect_score(self):
        """Test that all maximum values result in score of 1.0."""
        score = compute_contextual_integrity_score(
            alignment=1.0,
            plausibility=1.0,
            genealogy_consistency=1.0,
            source_reputation=1.0,
        )
        assert score == 1.0

    @pytest.mark.unit
    def test_compute_zero_score(self):
        """Test that all minimum values result in score of 0.0."""
        score = compute_contextual_integrity_score(
            alignment=0.0,
            plausibility=0.0,
            genealogy_consistency=0.0,
            source_reputation=0.0,
        )
        assert score == 0.0

    @pytest.mark.unit
    def test_compute_with_default_weights(self):
        """Test computation with default weights (60/15/15/10)."""
        score = compute_contextual_integrity_score(
            alignment=0.8,
            plausibility=0.6,
            genealogy_consistency=0.7,
            source_reputation=0.5,
        )
        # Expected: 0.6*0.8 + 0.15*0.6 + 0.15*0.7 + 0.1*0.5 = 0.48 + 0.09 + 0.105 + 0.05 = 0.725
        assert score == pytest.approx(0.725, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_custom_weights(self):
        """Custom weights should shift the contextual integrity score."""
        weights = ContextualIntegrityWeights(
            alignment=0.3,
            plausibility=0.4,
            genealogy_consistency=0.2,
            source_reputation=0.1,
        )
        score = compute_contextual_integrity_score(
            alignment=0.2,
            plausibility=0.9,
            genealogy_consistency=0.5,
            source_reputation=0.5,
            weights=weights,
        )
        # Expected: 0.3*0.2 + 0.4*0.9 + 0.2*0.5 + 0.1*0.5 = 0.06 + 0.36 + 0.10 + 0.05 = 0.57
        assert score == pytest.approx(0.57, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_none_values(self):
        """Test that None values are treated as 0.0 (maintaining weight distribution)."""
        score = compute_contextual_integrity_score(
            alignment=0.8,
            plausibility=None,
            genealogy_consistency=None,
            source_reputation=None,
        )
        # None treated as 0.0, weights not renormalized:
        # Expected: 0.6*0.8 + 0.15*0.0 + 0.15*0.0 + 0.1*0.0 = 0.48
        assert score == pytest.approx(0.48, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_all_none(self):
        """Test that all None values result in 0.0."""
        score = compute_contextual_integrity_score(
            alignment=None,
            plausibility=None,
            genealogy_consistency=None,
            source_reputation=None,
        )
        assert score == 0.0

    @pytest.mark.unit
    def test_compute_clamps_high_values(self):
        """Test that values > 1.0 are clamped to 1.0."""
        score = compute_contextual_integrity_score(
            alignment=1.5,
            plausibility=2.0,
            genealogy_consistency=1.2,
            source_reputation=1.3,
        )
        assert score == 1.0

    @pytest.mark.unit
    def test_compute_clamps_negative_values(self):
        """Test that negative values are clamped to 0.0."""
        score = compute_contextual_integrity_score(
            alignment=-0.5,
            plausibility=-1.0,
            genealogy_consistency=-0.2,
            source_reputation=-0.3,
        )
        assert score == 0.0

    @pytest.mark.unit
    def test_alignment_dominates(self):
        """Alignment should dominate contextual integrity score."""
        score = compute_contextual_integrity_score(
            alignment=0.9,
            plausibility=0.2,
            genealogy_consistency=0.2,
            source_reputation=0.2,
        )
        assert score > 0.6

    @pytest.mark.unit
    def test_weights_immutable(self):
        """Test that ContextualIntegrityWeights dataclass is frozen."""
        weights = ContextualIntegrityWeights()
        with pytest.raises(AttributeError):
            weights.alignment = 0.5
