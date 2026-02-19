"""Tests for the MedContext Contextual Authenticity Score calculation."""

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
            veracity=1.0,
        )
        assert score == pytest.approx(1.0)

    @pytest.mark.unit
    def test_compute_zero_score(self):
        """Test that all minimum values result in score of 0.0."""
        score = compute_contextual_integrity_score(
            alignment=0.0,
            veracity=0.0,
        )
        assert score == pytest.approx(0.0)

    @pytest.mark.unit
    def test_compute_with_default_weights(self):
        """Test computation with default weights (50/50)."""
        score = compute_contextual_integrity_score(
            alignment=0.8,
            veracity=0.6,
        )
        # Expected: 0.5*0.8 + 0.5*0.6 = 0.4 + 0.3 = 0.7
        assert score == pytest.approx(0.7, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_custom_weights(self):
        """Custom weights should shift the contextual authenticity score."""
        weights = ContextualIntegrityWeights(
            alignment=0.7,
            veracity=0.3,
        )
        score = compute_contextual_integrity_score(
            alignment=0.2,
            veracity=0.9,
            weights=weights,
        )
        # Expected: 0.7*0.2 + 0.3*0.9 = 0.14 + 0.27 = 0.41
        assert score == pytest.approx(0.41, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_none_values(self):
        """Test that None values are treated as 0.0 (maintaining weight distribution)."""
        score = compute_contextual_integrity_score(
            alignment=0.8,
            veracity=None,
        )
        # None treated as 0.0, weights not renormalized:
        # Expected: 0.5*0.8 + 0.5*0.0 = 0.4
        assert score == pytest.approx(0.4, abs=0.001)

    @pytest.mark.unit
    def test_compute_with_all_none(self):
        """Test that all None values result in 0.0."""
        score = compute_contextual_integrity_score(
            alignment=None,
            veracity=None,
        )
        assert score == 0.0

    @pytest.mark.unit
    def test_compute_clamps_high_values(self):
        """Test that values > 1.0 are clamped to 1.0."""
        score = compute_contextual_integrity_score(
            alignment=1.5,
            veracity=2.0,
        )
        assert score == pytest.approx(1.0)

    @pytest.mark.unit
    def test_compute_clamps_negative_values(self):
        """Test that negative values are clamped to 0.0."""
        score = compute_contextual_integrity_score(
            alignment=-0.5,
            veracity=-1.0,
        )
        assert score == 0.0

    @pytest.mark.unit
    def test_alignment_dominates_when_weighted(self):
        """Alignment can be weighted to dominate contextual integrity score."""
        weights = ContextualIntegrityWeights(alignment=0.8, veracity=0.2)
        score = compute_contextual_integrity_score(
            alignment=0.9, veracity=0.2, weights=weights
        )
        # 0.8*0.9 + 0.2*0.2 = 0.72 + 0.04 = 0.76
        assert score > 0.7

    @pytest.mark.unit
    def test_weights_immutable(self):
        """Test that ContextualIntegrityWeights dataclass is frozen."""
        weights = ContextualIntegrityWeights()
        with pytest.raises(AttributeError):
            weights.alignment = 0.5
