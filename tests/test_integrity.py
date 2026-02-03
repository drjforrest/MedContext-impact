"""Tests for the MedContext Integrity Score calculation."""

import pytest

from app.metrics.integrity import (
    ContextualIntegrityWeights,
    IntegrityWeights,
    compute_contextual_integrity_score,
    compute_integrity_score,
)


class TestIntegrityScore:
    """Test suite for integrity score computation."""

    @pytest.mark.unit
    def test_compute_perfect_score(self):
        """Test that all maximum values result in score of 1.0."""
        score = compute_integrity_score(
            plausibility=1.0,
            genealogy_consistency=1.0,
            source_reputation=1.0,
        )
        assert score == 1.0

    @pytest.mark.unit
    def test_compute_zero_score(self):
        """Test that all minimum values result in score of 0.0."""
        score = compute_integrity_score(
            plausibility=0.0,
            genealogy_consistency=0.0,
            source_reputation=0.0,
        )
        assert score == 0.0

    @pytest.mark.unit
    def test_compute_with_default_weights(self):
        """Test computation with default weights."""
        score = compute_integrity_score(
            plausibility=0.8,
            genealogy_consistency=0.6,
            source_reputation=0.7,
        )
        # Expected: 0.4*0.8 + 0.3*0.6 + 0.3*0.7 = 0.32 + 0.18 + 0.21 = 0.71
        assert score == pytest.approx(0.71, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_custom_weights(self):
        """Test computation with custom weights."""
        weights = IntegrityWeights(
            plausibility=0.5,
            genealogy_consistency=0.3,
            source_reputation=0.2,
        )
        score = compute_integrity_score(
            plausibility=0.8,
            genealogy_consistency=0.6,
            source_reputation=0.7,
            weights=weights,
        )
        # Expected: 0.5*0.8 + 0.3*0.6 + 0.2*0.7 = 0.4 + 0.18 + 0.14 = 0.72
        assert score == pytest.approx(0.72, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_none_values(self):
        """Test that None values are treated as 0.0 (maintaining weight distribution)."""
        score = compute_integrity_score(
            plausibility=0.8,
            genealogy_consistency=None,
            source_reputation=None,
        )
        # None treated as 0.0, weights not renormalized:
        # Expected: 0.4*0.8 + 0.3*0.0 + 0.3*0.0 = 0.32
        assert score == pytest.approx(0.32, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_all_none(self):
        """Test that all None values result in 0.0."""
        score = compute_integrity_score(
            plausibility=None,
            genealogy_consistency=None,
            source_reputation=None,
        )
        assert score == 0.0

    @pytest.mark.unit
    def test_compute_clamps_high_values(self):
        """Test that values > 1.0 are clamped to 1.0."""
        score = compute_integrity_score(
            plausibility=1.5,
            genealogy_consistency=2.0,
            source_reputation=1.2,
        )
        assert score == 1.0

    @pytest.mark.unit
    def test_compute_clamps_negative_values(self):
        """Test that negative values are clamped to 0.0."""
        score = compute_integrity_score(
            plausibility=-0.5,
            genealogy_consistency=-1.0,
            source_reputation=-0.2,
        )
        assert score == 0.0

    @pytest.mark.unit
    def test_compute_partial_none_with_weights(self):
        """Test that None values contribute 0.0 (no weight renormalization)."""
        score = compute_integrity_score(
            plausibility=0.9,
            genealogy_consistency=None,
            source_reputation=0.6,
        )
        # None treated as 0.0, weights not renormalized:
        # Expected: 0.4*0.9 + 0.3*0.0 + 0.3*0.6 = 0.36 + 0.0 + 0.18 = 0.54
        assert score == pytest.approx(0.54, abs=0.001)

    @pytest.mark.unit
    def test_integrity_weights_immutable(self):
        """Test that IntegrityWeights dataclass is frozen."""
        weights = IntegrityWeights()
        with pytest.raises(AttributeError):
            weights.plausibility = 0.5

    @pytest.mark.unit
    def test_contextual_integrity_alignment_weighted(self):
        """Alignment should dominate contextual authenticity score."""
        score = compute_contextual_integrity_score(
            alignment=0.9,
            plausibility=0.2,
            genealogy_consistency=0.2,
            source_reputation=0.2,
        )
        assert score > 0.6

    @pytest.mark.unit
    def test_contextual_integrity_custom_weights(self):
        """Custom weights should shift the contextual authenticity score."""
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
        assert score > 0.5
