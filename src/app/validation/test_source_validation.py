#!/usr/bin/env python3
"""Test warning system for missing source data in sampling bias analysis.

This script creates synthetic test data with no source information to verify
that the warning and validation checks work correctly.
"""

import sys

from app.validation.sampling_bias import compute_distribution_stats


def test_missing_source_warning():
    """Test that warning is issued when all sources are 'unknown'."""
    # Create synthetic records with no source information
    records = [
        {
            "image_id": f"test_{i}",
            "image_path": f"/fake/path/image_{i}.jpg",
            "claim": "Test claim " * 100,  # Make it long enough
            "ground_truth": {
                "is_fake_claim": i % 2 == 0,  # Alternate true/false
            },
            # NO 'source' field - should default to 'unknown'
        }
        for i in range(10)
    ]

    print("=" * 70)
    print("Testing warning system for missing source data")
    print("=" * 70)
    print()
    print(f"Created {len(records)} synthetic records with no source field")
    print()

    # Capture stderr to verify warning is printed
    import io

    old_stderr = sys.stderr
    sys.stderr = io.StringIO()

    try:
        stats = compute_distribution_stats(records, "Test Dataset")

        # Get stderr output
        warning_output = sys.stderr.getvalue()
    finally:
        sys.stderr = old_stderr

    # Verify results
    print("Distribution stats computed:")
    print(f"  - Total samples: {stats['n_samples']}")
    print(f"  - Source distribution: {stats['source_distribution']}")
    print(f"  - Source metadata: {stats['source_metadata']}")
    print()

    # Check assertions
    assert stats["source_metadata"]["all_unknown"], "Expected all_unknown=True"
    assert (
        stats["source_metadata"]["total_sources"] == 1
    ), "Expected only 1 source (unknown)"
    assert stats["source_metadata"]["unknown_count"] == len(
        records
    ), "Expected all records to be unknown"
    assert stats["source_metadata"]["unknown_rate"] == 1.0, "Expected 100% unknown rate"
    assert (
        "unknown" in stats["source_distribution"]
    ), "Expected 'unknown' in source_distribution"
    assert stats["source_distribution"]["unknown"] == len(
        records
    ), "Expected all records counted as unknown"

    # Verify warning was printed
    assert "WARNING" in warning_output, "Expected WARNING in stderr"
    assert "unknown" in warning_output.lower(), "Expected 'unknown' in warning message"

    print("✅ All assertions passed!")
    print()
    print("Warning output (stderr):")
    print("-" * 70)
    print(warning_output)
    print("-" * 70)

    return True


def test_partial_source_data():
    """Test with partial source data (some known, some unknown)."""
    records = [
        {
            "image_id": f"test_{i}",
            "image_path": f"/fake/path/image_{i}.jpg",
            "claim": "Test claim " * 100,
            "source": "LeadStories" if i < 5 else "unknown",
            "ground_truth": {
                "is_fake_claim": True,
            },
        }
        for i in range(10)
    ]

    print()
    print("=" * 70)
    print("Testing with partial source data (50% known, 50% unknown)")
    print("=" * 70)
    print()

    stats = compute_distribution_stats(records, "Partial Source Dataset")

    print("Distribution stats:")
    print(f"  - Total samples: {stats['n_samples']}")
    print(f"  - Source distribution: {stats['source_distribution']}")
    print(f"  - Source metadata: {stats['source_metadata']}")
    print()

    # Verify results
    assert not stats["source_metadata"]["all_unknown"], "Expected all_unknown=False"
    assert stats["source_metadata"]["total_sources"] == 2, "Expected 2 sources"
    assert stats["source_metadata"]["unknown_count"] == 5, "Expected 5 unknown"
    assert stats["source_metadata"]["unknown_rate"] == 0.5, "Expected 50% unknown rate"
    assert "LeadStories" in stats["source_distribution"], "Expected LeadStories"
    assert "unknown" in stats["source_distribution"], "Expected unknown"

    print("✅ All assertions passed!")

    return True


def test_complete_source_data():
    """Test with complete source data (no unknown)."""
    records = [
        {
            "image_id": f"test_{i}",
            "image_path": f"/fake/path/image_{i}.jpg",
            "claim": "Test claim " * 100,
            "source": ["LeadStories", "Healthline", "Nih"][i % 3],
            "ground_truth": {
                "is_fake_claim": True,
            },
        }
        for i in range(12)
    ]

    print()
    print("=" * 70)
    print("Testing with complete source data (no unknown)")
    print("=" * 70)
    print()

    stats = compute_distribution_stats(records, "Complete Source Dataset")

    print("Distribution stats:")
    print(f"  - Total samples: {stats['n_samples']}")
    print(f"  - Source distribution: {stats['source_distribution']}")
    print(f"  - Source metadata: {stats['source_metadata']}")
    print()

    # Verify results
    assert not stats["source_metadata"]["all_unknown"], "Expected all_unknown=False"
    assert stats["source_metadata"]["total_sources"] == 3, "Expected 3 sources"
    assert stats["source_metadata"]["unknown_count"] == 0, "Expected 0 unknown"
    assert stats["source_metadata"]["unknown_rate"] == 0.0, "Expected 0% unknown rate"
    assert (
        "unknown" not in stats["source_distribution"]
    ), "Expected no 'unknown' in distribution"

    print("✅ All assertions passed!")

    return True


if __name__ == "__main__":
    print()
    print("Testing source data validation and warning system")
    print("=" * 70)

    all_passed = True

    try:
        all_passed &= test_missing_source_warning()
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    try:
        all_passed &= test_partial_source_data()
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    try:
        all_passed &= test_complete_source_data()
    except AssertionError as e:
        print(f"❌ Test failed: {e}")
        all_passed = False

    print()
    print("=" * 70)
    if all_passed:
        print("✅ ALL TESTS PASSED")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED")
        sys.exit(1)
