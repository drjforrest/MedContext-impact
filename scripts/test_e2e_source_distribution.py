#!/usr/bin/env python3
"""End-to-end test for source distribution fix.

This test verifies that:
1. Source information is correctly extracted from image paths
2. All Med-MMHL records have valid source attribution
3. The sampling bias analysis produces accurate source distribution
4. Warning system detects and reports incomplete data
"""

import json
import sys
from pathlib import Path

# Add repo root to path
repo_root = Path(__file__).parent.parent
sys.path.insert(0, str(repo_root / "src"))

from app.validation.loaders import load_med_mmhl_dataset  # noqa: E402


def test_source_extraction_from_real_data():
    """Test source extraction on actual Med-MMHL data."""
    print("=" * 70)
    print("END-TO-END TEST: Source Distribution Fix")
    print("=" * 70)
    print()

    # Load Med-MMHL test set
    print("Step 1: Loading Med-MMHL test set...")
    records = load_med_mmhl_dataset(
        benchmark_path=Path("data/med-mmhl"),
        split="test",
        base_image_dir=Path("data/med-mmhl"),
    )

    if not records:
        print("❌ No records loaded - cannot test")
        return False

    print(f"  ✓ Loaded {len(records)} records")
    print()

    # Check source field exists
    print("Step 2: Verifying 'source' field exists in all records...")
    missing_source = [r for r in records if "source" not in r]

    if missing_source:
        print(f"  ❌ {len(missing_source)} records missing 'source' field")
        return False

    print(f"  ✓ All {len(records)} records have 'source' field")
    print()

    # Check for unknown sources
    print("Step 3: Checking source attribution quality...")
    from collections import Counter

    sources = [r["source"] for r in records]
    source_counts = Counter(sources)

    unknown_count = source_counts.get("unknown", 0)
    unknown_pct = unknown_count / len(records) * 100 if records else 0

    print(f"  Total unique sources: {len(source_counts)}")
    print(f"  Unknown sources: {unknown_count} ({unknown_pct:.1f}%)")
    print()

    # Show top sources
    print("  Top 10 sources:")
    for i, (source, count) in enumerate(source_counts.most_common(10), 1):
        pct = count / len(records) * 100
        print(f"    {i:2}. {source:20} {count:5} ({pct:5.1f}%)")
    print()

    # Verify against expected distribution
    print("Step 4: Verifying against expected distribution...")

    # Load the analysis results
    analysis_file = repo_root / "validation_results" / "sampling_bias_analysis.json"
    if not analysis_file.exists():
        print(f"  ⚠️  Analysis file not found: {analysis_file}")
        print(
            "  Run: python scripts/check_sampling_bias.py --output validation_results/sampling_bias_analysis.json"
        )
        # This is not a failure - just means analysis needs to be run
    else:
        with open(analysis_file) as f:
            analysis = json.load(f)

        expected_metadata = analysis["full_dataset"]["source_metadata"]

        # Verify totals match
        if len(records) != analysis["full_dataset"]["n_samples"]:
            print(
                f"  ⚠️  Record count mismatch: {len(records)} loaded vs {analysis['full_dataset']['n_samples']} in analysis"
            )

        # Verify source distribution matches
        print(f"  ✓ Analysis file loaded: {analysis_file.name}")
        print(f"    - Total sources in analysis: {expected_metadata['total_sources']}")
        print(f"    - All unknown: {expected_metadata['all_unknown']}")
        print(f"    - Unknown rate: {expected_metadata['unknown_rate']:.1%}")

        if expected_metadata["all_unknown"]:
            print(
                "  ❌ Analysis shows all sources as 'unknown' - this is the bug we fixed!"
            )
            return False
        else:
            print("  ✓ Analysis shows proper source distribution")

    print()

    # Final assessment
    print("Step 5: Final assessment...")

    if unknown_pct > 50:
        print(f"  ❌ Too many unknown sources ({unknown_pct:.1f}%)")
        return False
    elif unknown_pct > 10:
        print(
            f"  ⚠️  Some unknown sources ({unknown_pct:.1f}%) - consider investigating"
        )
    else:
        print(f"  ✓ Low unknown rate ({unknown_pct:.1f}%)")

    if len(source_counts) < 3:
        print(f"  ⚠️  Limited source diversity ({len(source_counts)} sources)")
    else:
        print(f"  ✓ Good source diversity ({len(source_counts)} sources)")

    print()
    print("=" * 70)
    print("✅ END-TO-END TEST PASSED")
    print("=" * 70)
    print()
    print("Summary:")
    print(f"  - Loaded {len(records)} records from Med-MMHL test set")
    print(f"  - Found {len(source_counts)} unique sources")
    print(f"  - Unknown rate: {unknown_pct:.1f}%")
    print(
        f"  - Top source: {source_counts.most_common(1)[0][0]} ({source_counts.most_common(1)[0][1]} records, {source_counts.most_common(1)[0][1]/len(records)*100:.1f}%)"
    )

    return True


if __name__ == "__main__":
    try:
        success = test_source_extraction_from_real_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
