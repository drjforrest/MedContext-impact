#!/usr/bin/env python3
"""Unit tests for sampling bias analysis.

Tests the source overlap calculation logic to ensure:
1. Identical distributions return 1.0 (perfect overlap)
2. Completely disjoint distributions return 0.0
3. Partial overlaps return appropriate Jaccard similarity
4. Edge cases are handled correctly
"""


import pytest

from app.validation.sampling_bias import (
    compare_distributions,
    compute_distribution_stats,
)


class TestSourceOverlapCalculation:
    """Tests for top_source_overlap metric using Jaccard similarity."""

    def test_identical_single_source_returns_1_0(self):
        """When both datasets have only 'unknown', overlap should be 1.0 (perfect match)."""
        full_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {"unknown": 100},
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }
        subset_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {"unknown": 50},
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }

        result = compare_distributions(full_stats, subset_stats)

        assert (
            result["source_bias"]["top_source_overlap"] == 1.0
        ), "Identical single-source distributions should have 1.0 overlap"
        assert result["source_bias"]["assessment"] == "ACCEPTABLE"

    def test_identical_multiple_sources_returns_1_0(self):
        """When both datasets have identical top sources, overlap should be 1.0."""
        full_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_a": 50,
                "source_b": 30,
                "source_c": 20,
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }
        subset_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_a": 25,
                "source_b": 15,
                "source_c": 10,
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }

        result = compare_distributions(full_stats, subset_stats)

        assert (
            result["source_bias"]["top_source_overlap"] == 1.0
        ), "Identical multi-source distributions should have 1.0 overlap"
        assert result["source_bias"]["assessment"] == "ACCEPTABLE"

    def test_completely_disjoint_sources_returns_0_0(self):
        """When datasets have no common sources, overlap should be 0.0."""
        full_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_a": 50,
                "source_b": 30,
                "source_c": 20,
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }
        subset_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_x": 25,
                "source_y": 15,
                "source_z": 10,
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }

        result = compare_distributions(full_stats, subset_stats)

        assert (
            result["source_bias"]["top_source_overlap"] == 0.0
        ), "Completely disjoint source distributions should have 0.0 overlap"
        assert result["source_bias"]["assessment"] == "POTENTIAL_BIAS"

    def test_partial_overlap_returns_correct_jaccard(self):
        """Partial overlaps should return correct Jaccard similarity."""
        full_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_a": 50,
                "source_b": 30,
                "source_c": 20,
                "source_d": 10,
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }
        subset_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_a": 25,  # overlap
                "source_b": 15,  # overlap
                "source_x": 10,  # unique to subset
                "source_y": 5,  # unique to subset
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }

        result = compare_distributions(full_stats, subset_stats)

        # Jaccard = |intersection| / |union|
        # intersection = {source_a, source_b} = 2
        # union = {source_a, source_b, source_c, source_d, source_x, source_y} = 6
        # Jaccard = 2/6 = 0.333...
        expected_overlap = 2 / 6

        assert (
            abs(result["source_bias"]["top_source_overlap"] - expected_overlap) < 0.001
        ), f"Expected Jaccard similarity {expected_overlap:.3f}, got {result['source_bias']['top_source_overlap']:.3f}"
        assert (
            result["source_bias"]["assessment"] == "POTENTIAL_BIAS"
        )  # < 0.6 threshold

    def test_high_partial_overlap_returns_acceptable(self):
        """High overlap (>=0.6) should return ACCEPTABLE assessment."""
        full_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_a": 50,
                "source_b": 30,
                "source_c": 20,
                "source_d": 10,
                "source_e": 5,
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }
        subset_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_a": 25,  # overlap
                "source_b": 15,  # overlap
                "source_c": 10,  # overlap
                "source_d": 5,  # overlap
                "source_x": 3,  # unique to subset
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }

        result = compare_distributions(full_stats, subset_stats)

        # Jaccard = |intersection| / |union|
        # intersection = {source_a, source_b, source_c, source_d} = 4
        # union = {source_a, source_b, source_c, source_d, source_e, source_x} = 6
        # Jaccard = 4/6 = 0.666... > 0.6
        expected_overlap = 4 / 6

        assert (
            abs(result["source_bias"]["top_source_overlap"] - expected_overlap) < 0.001
        )
        assert result["source_bias"]["assessment"] == "ACCEPTABLE"

    def test_all_unknown_sources_returns_none(self):
        """When all sources are 'unknown', overlap should be None and assessment UNAVAILABLE."""
        full_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {"unknown": 100},
            "source_metadata": {"all_unknown": True},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }
        subset_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {"unknown": 50},
            "source_metadata": {"all_unknown": True},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }

        result = compare_distributions(full_stats, subset_stats)

        assert (
            result["source_bias"]["top_source_overlap"] is None
        ), "When all sources are 'unknown', overlap should be None"
        assert result["source_bias"]["assessment"] == "UNAVAILABLE"

    def test_empty_source_distribution_returns_1_0(self):
        """Edge case: Empty source sets should return 1.0 (both empty = identical)."""
        full_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {},
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }
        subset_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {},
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }

        result = compare_distributions(full_stats, subset_stats)

        assert (
            result["source_bias"]["top_source_overlap"] == 1.0
        ), "Empty source sets should have 1.0 overlap (both empty = identical)"

    def test_top_5_sources_only(self):
        """Only top 5 sources should be considered for overlap calculation."""
        full_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_1": 100,
                "source_2": 90,
                "source_3": 80,
                "source_4": 70,
                "source_5": 60,
                "source_6": 50,  # Should be ignored (outside top 5)
                "source_7": 40,  # Should be ignored
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }
        subset_stats = {
            "label_distribution": {"misinformation_rate": 0.5},
            "source_distribution": {
                "source_1": 50,
                "source_2": 45,
                "source_3": 40,
                "source_4": 35,
                "source_5": 30,
                "source_6": 25,  # Not in top 5 (6th by count)
            },
            "source_metadata": {"all_unknown": False},
            "claim_length": {"mean": 1000},
            "duplicate_rate": 0.0,
        }

        result = compare_distributions(full_stats, subset_stats)

        # Full top 5: {source_1, source_2, source_3, source_4, source_5}
        # Subset top 5: {source_1, source_2, source_3, source_4, source_5}
        # (source_6 is 6th in full dataset, but 5th in subset - subset takes its own top 5)
        # Wait, let me recalculate:
        # Full top 5 by count: source_1(100), source_2(90), source_3(80), source_4(70), source_5(60)
        # Subset top 5 by count: source_1(50), source_2(45), source_3(40), source_4(35), source_5(30)
        # Intersection: all 5 sources
        # Union: 5 sources
        # Jaccard: 5/5 = 1.0

        assert result["source_bias"]["top_source_overlap"] == 1.0


class TestComputeDistributionStats:
    """Tests for compute_distribution_stats helper function."""

    def test_basic_stats_computation(self):
        """Test that basic statistics are computed correctly."""
        records = [
            {
                "ground_truth": {"is_fake_claim": True},
                "source": "source_a",
                "claim": "This is a claim",
                "image_id": "img_1",
            },
            {
                "ground_truth": {"is_fake_claim": False},
                "source": "source_b",
                "claim": "Another claim",
                "image_id": "img_2",
            },
            {
                "ground_truth": {"is_fake_claim": True},
                "source": "source_a",
                "claim": "Third claim",
                "image_id": "img_3",
            },
        ]

        stats = compute_distribution_stats(records, "Test Dataset")

        assert stats["name"] == "Test Dataset"
        assert stats["n_samples"] == 3
        assert stats["label_distribution"]["misinformation"] == 2
        assert stats["label_distribution"]["real"] == 1
        assert abs(stats["label_distribution"]["misinformation_rate"] - 2 / 3) < 0.001
        assert stats["source_distribution"]["source_a"] == 2
        assert stats["source_distribution"]["source_b"] == 1
        assert stats["unique_images"] == 3
        assert stats["duplicate_rate"] == 0.0

    def test_unknown_source_detection(self):
        """Test that all-unknown sources are properly detected."""
        records = [
            {
                "ground_truth": {"is_fake_claim": True},
                "source": "unknown",
                "claim": "Claim 1",
                "image_id": "img_1",
            },
            {
                "ground_truth": {"is_fake_claim": False},
                "source": "unknown",
                "claim": "Claim 2",
                "image_id": "img_2",
            },
        ]

        stats = compute_distribution_stats(records, "Unknown Sources")

        assert stats["source_metadata"]["all_unknown"] is True
        assert stats["source_metadata"]["unknown_count"] == 2
        assert stats["source_metadata"]["unknown_rate"] == 1.0

    def test_duplicate_detection(self):
        """Test that image duplicates are detected correctly."""
        records = [
            {
                "ground_truth": {"is_fake_claim": True},
                "source": "source_a",
                "claim": "Claim 1",
                "image_id": "img_1",
            },
            {
                "ground_truth": {"is_fake_claim": False},
                "source": "source_b",
                "claim": "Claim 2",
                "image_id": "img_1",  # Duplicate
            },
            {
                "ground_truth": {"is_fake_claim": True},
                "source": "source_a",
                "claim": "Claim 3",
                "image_id": "img_2",
            },
        ]

        stats = compute_distribution_stats(records, "With Duplicates")

        assert stats["unique_images"] == 2
        assert abs(stats["duplicate_rate"] - 1 / 3) < 0.001  # 1 duplicate out of 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
