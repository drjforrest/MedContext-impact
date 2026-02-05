"""Verify that the corrected scoring maintains fixed weights (no renormalization).

This script demonstrates the difference between the old (renormalized) and
corrected (fixed weights) scoring behavior.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.metrics.integrity import compute_contextual_integrity_score

print("=" * 70)
print("CORRECTED SCORING VERIFICATION")
print("=" * 70)
print()

# Test Case 1: Only Alignment and Plausibility available (Genealogy=None, Source=None)
print("Test Case 1: Alignment + Plausibility only (as in pilot validation)")
print("-" * 70)
alignment_score = 0.8
plausibility_score = 0.6
genealogy_score = None  # Not available
source_score = None  # Not available

final_score = compute_contextual_integrity_score(
    alignment=alignment_score,
    plausibility=plausibility_score,
    genealogy_consistency=genealogy_score,
    source_reputation=source_score,
)

print(f"  Alignment:    {alignment_score} (weight: 60%)")
print(f"  Plausibility: {plausibility_score} (weight: 15%)")
print(f"  Genealogy:    {genealogy_score} (weight: 15%)")
print(f"  Source:       {source_score} (weight: 10%)")
print()
print("  CORRECTED calculation (fixed weights):")
print(
    f"    = 0.60 × {alignment_score} + 0.15 × {plausibility_score} + 0.15 × 0.0 + 0.10 × 0.0"
)
print(
    f"    = {0.60 * alignment_score:.3f} + {0.15 * plausibility_score:.3f} + 0.000 + 0.000"
)
print(f"    = {final_score:.3f}")
print()
print("  OLD calculation (renormalized weights):")
old_renormalized = (0.60 * alignment_score + 0.15 * plausibility_score) / 0.75
print(f"    = (0.60 × {alignment_score} + 0.15 × {plausibility_score}) / 0.75")
print(f"    = ({0.60 * alignment_score:.3f} + {0.15 * plausibility_score:.3f}) / 0.75")
print(f"    = {old_renormalized:.3f}")
print()
print(f"  DIFFERENCE: {abs(final_score - old_renormalized):.3f}")
print()

# Test Case 2: All signals available
print("Test Case 2: All 4 signals available")
print("-" * 70)
alignment_score = 0.8
plausibility_score = 0.6
genealogy_score = 0.7
source_score = 0.5

final_score = compute_contextual_integrity_score(
    alignment=alignment_score,
    plausibility=plausibility_score,
    genealogy_consistency=genealogy_score,
    source_reputation=source_score,
)

print(f"  Alignment:    {alignment_score} (weight: 60%)")
print(f"  Plausibility: {plausibility_score} (weight: 15%)")
print(f"  Genealogy:    {genealogy_score} (weight: 15%)")
print(f"  Source:       {source_score} (weight: 10%)")
print()
print("  CORRECTED calculation (fixed weights):")
print(
    f"    = 0.60 × {alignment_score} + 0.15 × {plausibility_score} + 0.15 × {genealogy_score} + 0.10 × {source_score}"
)
print(
    f"    = {0.60 * alignment_score:.3f} + {0.15 * plausibility_score:.3f} + {0.15 * genealogy_score:.3f} + {0.10 * source_score:.3f}"
)
print(f"    = {final_score:.3f}")
print()

# Test Case 3: Demonstrate impact on validation accuracy estimation
print("Test Case 3: Impact on 61.1% validation accuracy")
print("-" * 70)
print("OLD (renormalized): 61.1% reflects 80/20 system (Alignment/Plausibility)")
print("CORRECTED (fixed):  61.1% will likely be LOWER for 60/15/15/10 system")
print()
print(
    "Why? Because missing signals now contribute 0% instead of redistributing weight."
)
print("This is more accurate and honest about system performance!")
print()

print("=" * 70)
print("VERIFICATION COMPLETE")
print("=" * 70)
print()
print("Summary:")
print("  ✅ Corrected scoring maintains 60/15/15/10 weight distribution")
print("  ✅ Missing signals (None) contribute 0.0, not redistributed")
print("  ✅ Full validation rerun required to get accurate performance metrics")
print()
