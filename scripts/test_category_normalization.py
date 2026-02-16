#!/usr/bin/env python3
"""Standalone test for category normalization.

Verifies that chart_data.json files have properly normalized categories
without pipe-separated values.
"""

import json
import sys
from pathlib import Path


def test_chart_data_categories():
    """Test that chart_data.json files have no pipe-separated categories."""
    validation_results = Path("validation_results")

    if not validation_results.exists():
        print("⚠️  No validation_results directory found")
        return True

    chart_files = list(validation_results.glob("**/chart_data.json"))
    if not chart_files:
        print("⚠️  No chart_data.json files found")
        return True

    print(f"Testing {len(chart_files)} chart_data.json file(s)...\n")

    all_passed = True

    for chart_file in chart_files:
        try:
            display_path = chart_file.relative_to(Path.cwd())
        except ValueError:
            display_path = chart_file
        print(f"📄 {display_path}")

        with open(chart_file, "r") as f:
            data = json.load(f)

        file_passed = True

        # Check veracity_distribution
        if "veracity_distribution" in data:
            veracity_issues = []
            for i, entry in enumerate(data["veracity_distribution"]):
                category = entry.get("category", "")
                score = entry.get("score")

                # Check for pipe-separated values
                if "|" in category:
                    veracity_issues.append(
                        f"  ❌ veracity[{i}]: pipe-separated category '{category}' (score={score})"
                    )
                    file_passed = False

                # Check valid discrete values
                elif category not in ["true", "partially_true", "false"]:
                    veracity_issues.append(
                        f"  ⚠️  veracity[{i}]: unexpected category '{category}' (score={score})"
                    )

            if veracity_issues:
                print("\n".join(veracity_issues))
            else:
                print(
                    f"  ✅ veracity_distribution: {len(data['veracity_distribution'])} entries OK"
                )

        # Check alignment_distribution
        if "alignment_distribution" in data:
            alignment_issues = []
            for i, entry in enumerate(data["alignment_distribution"]):
                category = entry.get("category", "")
                score = entry.get("score")

                # Check for pipe-separated values
                if "|" in category:
                    alignment_issues.append(
                        f"  ❌ alignment[{i}]: pipe-separated category '{category}' (score={score})"
                    )
                    file_passed = False

                # Check valid discrete values
                elif category not in [
                    "aligns_fully",
                    "partially_aligns",
                    "does_not_align",
                ]:
                    alignment_issues.append(
                        f"  ⚠️  alignment[{i}]: unexpected category '{category}' (score={score})"
                    )

            if alignment_issues:
                print("\n".join(alignment_issues))
            else:
                print(
                    f"  ✅ alignment_distribution: {len(data['alignment_distribution'])} entries OK"
                )

        if file_passed:
            print("  ✅ All categories properly normalized")
        else:
            all_passed = False

        print()

    return all_passed


def main():
    print("=" * 70)
    print("CATEGORY NORMALIZATION TEST")
    print("=" * 70)
    print()

    passed = test_chart_data_categories()

    print("=" * 70)
    if passed:
        print("✅ ALL TESTS PASSED")
        print("=" * 70)
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("=" * 70)
        return 1


if __name__ == "__main__":
    sys.exit(main())
