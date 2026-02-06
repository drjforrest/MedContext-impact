#!/usr/bin/env python3
"""Test the specific scenario mentioned in the requirements: authentic images with false claims."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from validate_three_methods import ThreeMethodValidator


def test_authentic_image_false_claim_scenario():
    """Test the specific scenario: authentic images + false claims produce misinformation."""

    # Create a dummy validator instance
    validator = ThreeMethodValidator(Path("dummy"), Path("dummy"))

    print("Testing the specific scenario from requirements:")
    print("Authentic images with false claims should produce misinformation")
    print(
        "Previously: combined_analysis would set is_misinformation based only on pixel_authentic"
    )
    print(
        "After fix: combined_analysis should consider contextual_analysis signals as well"
    )
    print()

    # Simulate the scenario from the requirements:
    # - Authentic image (pixel_authentic = True)
    # - Contextual indicators showing low veracity or is_misleading = True
    pixel_result = {
        "pixel_authentic": True,  # Authentic image
        "confidence": 0.85,
        "method": "pixel_forensics",
        "file_size": 101275,
    }

    # Scenario 1: Authentic image with low veracity claim
    context_result = {
        "veracity_score": 0.3,  # Low veracity (false claim)
        "alignment_score": 0.4,  # Poor alignment
        "overall_score": 0.35,
        "is_misleading": False,  # Original logic would miss this
        "method": "contextual_analysis",
        "veracity_category": "false",  # False claim
        "alignment_category": "does_not_align",  # Poor alignment
    }

    print("Scenario 1: Authentic image with false claim")
    print(f"  pixel_authentic: {pixel_result['pixel_authentic']}")
    print(f"  veracity_score: {context_result['veracity_score']}")
    print(f"  veracity_category: {context_result['veracity_category']}")
    print(f"  alignment_score: {context_result['alignment_score']}")
    print(f"  alignment_category: {context_result['alignment_category']}")
    print(f"  is_misleading: {context_result['is_misleading']}")

    combined_result = validator.combined_analysis(pixel_result, context_result)
    print(
        f"  OLD LOGIC would give is_misinformation: {not pixel_result['pixel_authentic'] or context_result['is_misleading']}"
    )
    print(
        f"  NEW LOGIC gives is_misinformation: {combined_result['is_misinformation']}"
    )
    print(f"  NEW LOGIC gives is_misleading: {combined_result['is_misleading']}")
    print(f"  NEW LOGIC gives overall_score: {combined_result['overall_score']}")
    print()

    # Scenario 2: Authentic image with partially true claim but low scores (the edge case)
    pixel_result2 = {
        "pixel_authentic": True,  # Still authentic image
        "confidence": 0.85,
        "method": "pixel_forensics",
        "file_size": 101275,
    }

    context_result2 = {
        "veracity_score": 0.5,  # Neutral score
        "alignment_score": 0.5,  # Neutral score
        "overall_score": 0.5,
        "is_misleading": False,  # Would be missed by old logic
        "method": "contextual_analysis",
        "veracity_category": "partially_true",  # This matters now
        "alignment_category": "partially_aligns",  # This matters now
    }

    print("Scenario 2: Authentic image with partially true claim (edge case)")
    print(f"  pixel_authentic: {pixel_result2['pixel_authentic']}")
    print(f"  veracity_score: {context_result2['veracity_score']}")
    print(f"  veracity_category: {context_result2['veracity_category']}")
    print(f"  alignment_score: {context_result2['alignment_score']}")
    print(f"  alignment_category: {context_result2['alignment_category']}")
    print(f"  is_misleading: {context_result2['is_misleading']}")

    combined_result2 = validator.combined_analysis(pixel_result2, context_result2)
    print(
        f"  OLD LOGIC would give is_misinformation: {not pixel_result2['pixel_authentic'] or context_result2['is_misleading']}"
    )
    print(
        f"  NEW LOGIC gives is_misinformation: {combined_result2['is_misinformation']}"
    )
    print(f"  NEW LOGIC gives is_misleading: {combined_result2['is_misleading']}")
    print(f"  NEW LOGIC gives overall_score: {combined_result2['overall_score']}")
    print()

    # Verify the fix works
    assert combined_result["is_misinformation"], (
        "Scenario 1: Should detect misinformation"
    )
    assert combined_result2["is_misinformation"], (
        "Scenario 2: Should detect misinformation in edge case"
    )

    print("✅ SUCCESS: The fix correctly handles both scenarios!")
    print("   - Authentic images with clearly false claims are flagged")
    print(
        "   - Authentic images with partially true claims (but low scores) are flagged"
    )
    print(
        "   - Combined analysis now properly fuses contextual and pixel forensics signals"
    )


if __name__ == "__main__":
    test_authentic_image_false_claim_scenario()
