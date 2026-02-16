#!/usr/bin/env python3
"""Test is_misinformation decision logic.

Validates the veracity-first decision rule in combined_analysis.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from validate_three_methods import ThreeMethodValidator


def test_is_misinformation_logic():
    """Test the is_misinformation decision logic with various input combinations.

    Decision rule (veracity-first):
    1. veracity="false" OR veracity_score < 0.5 → is_misinformation=TRUE
    2. veracity="true" AND veracity_score >= 0.8 → is_misinformation=FALSE (regardless of alignment)
    3. Otherwise (veracity ambiguous), use alignment as tiebreaker:
       - alignment="does_not_align" OR alignment_score < 0.5 → is_misinformation=TRUE
       - alignment="aligns_fully" OR alignment_score >= 0.8 → is_misinformation=FALSE
       - Otherwise → is_misinformation=TRUE (default conservative)
    """
    # Create a validator instance (we only need the combined_analysis method)
    validator = ThreeMethodValidator(
        dataset_path=Path("/tmp/dummy.json"), output_dir=Path("/tmp/dummy_output")
    )

    test_cases = [
        # Case 1: High veracity, low alignment → NOT misinformation (veracity wins)
        {
            "name": "med_mmhl_test_265_0 scenario",
            "context": {
                "veracity_score": 0.9,
                "veracity_category": "true",
                "alignment_score": 0.1,
                "alignment_category": "does_not_align",
                "overall_score": 0.5,
                "is_misleading": False,
            },
            "pixel": {"pixel_authentic": False},
            "expected_is_misinformation": False,
            "reason": "High-confidence true claim overrides poor alignment",
        },
        # Case 2: Low veracity → always misinformation
        {
            "name": "False claim with good alignment",
            "context": {
                "veracity_score": 0.1,
                "veracity_category": "false",
                "alignment_score": 0.9,
                "alignment_category": "aligns_fully",
                "overall_score": 0.5,
                "is_misleading": False,
            },
            "pixel": {"pixel_authentic": True},
            "expected_is_misinformation": True,
            "reason": "False claim is always misinformation",
        },
        # Case 3: High veracity + high alignment → NOT misinformation
        {
            "name": "Both high",
            "context": {
                "veracity_score": 0.9,
                "veracity_category": "true",
                "alignment_score": 0.9,
                "alignment_category": "aligns_fully",
                "overall_score": 0.9,
                "is_misleading": False,
            },
            "pixel": {"pixel_authentic": True},
            "expected_is_misinformation": False,
            "reason": "Strong signals in both dimensions",
        },
        # Case 4: Partially true + does not align → misinformation
        {
            "name": "Ambiguous veracity, poor alignment",
            "context": {
                "veracity_score": 0.6,
                "veracity_category": "partially_true",
                "alignment_score": 0.1,
                "alignment_category": "does_not_align",
                "overall_score": 0.4,
                "is_misleading": True,
            },
            "pixel": {"pixel_authentic": True},
            "expected_is_misinformation": True,
            "reason": "Ambiguous veracity + poor alignment = misleading",
        },
        # Case 5: Partially true + aligns fully → NOT misinformation
        {
            "name": "Ambiguous veracity, good alignment",
            "context": {
                "veracity_score": 0.6,
                "veracity_category": "partially_true",
                "alignment_score": 0.9,
                "alignment_category": "aligns_fully",
                "overall_score": 0.7,
                "is_misleading": False,
            },
            "pixel": {"pixel_authentic": True},
            "expected_is_misinformation": False,
            "reason": "Ambiguous veracity but strong alignment saves it",
        },
        # Case 6: Both ambiguous → misinformation (conservative default)
        {
            "name": "Both ambiguous",
            "context": {
                "veracity_score": 0.6,
                "veracity_category": "partially_true",
                "alignment_score": 0.6,
                "alignment_category": "partially_aligns",
                "overall_score": 0.6,
                "is_misleading": False,
            },
            "pixel": {"pixel_authentic": True},
            "expected_is_misinformation": True,
            "reason": "Conservative default when both are ambiguous",
        },
    ]

    print("\n" + "=" * 80)
    print("IS_MISINFORMATION DECISION LOGIC TESTS")
    print("=" * 80 + "\n")

    passed = 0
    failed = 0

    for i, test in enumerate(test_cases, 1):
        result = validator.combined_analysis(test["pixel"], test["context"])
        actual = result["is_misinformation"]
        expected = test["expected_is_misinformation"]

        status = "✅ PASS" if actual == expected else "❌ FAIL"
        if actual == expected:
            passed += 1
        else:
            failed += 1

        print(f"Test {i}: {test['name']}")
        print(
            f"  Veracity: {test['context']['veracity_category']} ({test['context']['veracity_score']})"
        )
        print(
            f"  Alignment: {test['context']['alignment_category']} ({test['context']['alignment_score']})"
        )
        print(f"  Expected: is_misinformation={expected}")
        print(f"  Actual:   is_misinformation={actual}")
        print(f"  Reason:   {test['reason']}")
        print(f"  {status}\n")

    print("=" * 80)
    print(f"Results: {passed} passed, {failed} failed")
    print("=" * 80 + "\n")

    return failed == 0


if __name__ == "__main__":
    success = test_is_misinformation_logic()
    sys.exit(0 if success else 1)
