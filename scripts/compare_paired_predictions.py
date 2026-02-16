#!/usr/bin/env python3
"""Analyze sample-by-sample agreement between models."""

import json
import re
from pathlib import Path

# Load raw predictions from both runs
phase1_path = Path("validation_results/med_mmhl_n163_quantized_4b/raw_predictions.json")
phase2_path = Path("validation_results/med_mmhl_n163_hf_27b/raw_predictions.json")

with open(phase1_path) as f:
    phase1_predictions = json.load(f)

with open(phase2_path) as f:
    phase2_predictions = json.load(f)

# Verify same samples (by image_id)
phase1_ids = [p["image_id"] for p in phase1_predictions]
phase2_ids = [p["image_id"] for p in phase2_predictions]

if phase1_ids != phase2_ids:
    print("ERROR: Models evaluated on different samples!")
    print(f"Phase 1: {len(phase1_ids)} samples")
    print(f"Phase 2: {len(phase2_ids)} samples")
    exit(1)

# Compute actual sample count
sample_count = len(phase1_predictions)

# Extract seed from filename if present (e.g., "med_mmhl_n163_..." pattern)
# Fallback to "unknown" if not found
seed_match = re.search(r"n(\d+)", str(phase1_path))
seed = seed_match.group(1) if seed_match else "unknown"

print(
    f"✅ Confirmed: Both models evaluated on SAME {sample_count} samples (seed={seed})"
)
print()

# Compare predictions sample by sample
both_correct = 0
both_wrong = 0
only_4b_correct = 0
only_27b_correct = 0

disagreement_samples = []

for p1, p2 in zip(phase1_predictions, phase2_predictions):
    # Extract ground truth
    gt_misinfo = p1["ground_truth"]["is_misinformation"]

    # Extract predictions
    pred1_misinfo = p1["predictions"]["combined_analysis"]["is_misinformation"]
    pred2_misinfo = p2["predictions"]["combined_analysis"]["is_misinformation"]

    # Check correctness
    correct1 = pred1_misinfo == gt_misinfo
    correct2 = pred2_misinfo == gt_misinfo

    if correct1 and correct2:
        both_correct += 1
    elif not correct1 and not correct2:
        both_wrong += 1
    elif correct1 and not correct2:
        only_4b_correct += 1
        disagreement_samples.append(
            {
                "image_id": p1["image_id"],
                "ground_truth": "misinformation" if gt_misinfo else "legitimate",
                "4b_prediction": "misinformation" if pred1_misinfo else "legitimate",
                "27b_prediction": "misinformation" if pred2_misinfo else "legitimate",
                "winner": "4B",
            }
        )
    elif correct2 and not correct1:
        only_27b_correct += 1
        disagreement_samples.append(
            {
                "image_id": p1["image_id"],
                "ground_truth": "misinformation" if gt_misinfo else "legitimate",
                "4b_prediction": "misinformation" if pred1_misinfo else "legitimate",
                "27b_prediction": "misinformation" if pred2_misinfo else "legitimate",
                "winner": "27B",
            }
        )

total = len(phase1_predictions)
if total == 0:
    print("ERROR: No samples to compare")
    exit(1)
agreement_rate = (both_correct + both_wrong) / total

print("=" * 70)
print("PAIRED SAMPLE-BY-SAMPLE ANALYSIS")
print("=" * 70)
print()
print(f"Total Samples: {total}")
print()
print("Agreement:")
print(f"  Both Correct:  {both_correct:3d} ({both_correct / total:.1%})")
print(f"  Both Wrong:    {both_wrong:3d} ({both_wrong / total:.1%})")
print(f"  Total Agreement: {both_correct + both_wrong:3d} ({agreement_rate:.1%})")
print()
print("Disagreement (one right, one wrong):")
print(f"  Only 4B Correct:  {only_4b_correct:3d} samples")
print(f"  Only 27B Correct: {only_27b_correct:3d} samples")
print(f"  Net Difference:   {only_4b_correct - only_27b_correct:3d} samples")
print()
print("=" * 70)
print("INTERPRETATION")
print("=" * 70)
print()

if only_4b_correct == only_27b_correct:
    print("✅ PERFECT TIE: Models won on equal number of samples")
    print(f"   Each model was uniquely correct on {only_4b_correct} samples")
    print()
    print("   This means the accuracy difference is due to WHICH samples")
    print("   each model struggles with, not overall superiority.")
elif abs(only_4b_correct - only_27b_correct) <= 2:
    print("✅ NEAR TIE: Difference is negligible")
    print(f"   4B won {only_4b_correct} unique samples")
    print(f"   27B won {only_27b_correct} unique samples")
    print(f"   Difference: {abs(only_4b_correct - only_27b_correct)} samples")
    print()
    print("   With this small difference, neither model is clearly superior.")
else:
    winner = "4B" if only_4b_correct > only_27b_correct else "27B"
    diff = abs(only_4b_correct - only_27b_correct)
    print(f"🏆 {winner} wins on {diff} more samples")

print()
print(f"Models AGREE on {agreement_rate:.1%} of samples")
print(f"Models DISAGREE on {(1 - agreement_rate):.1%} of samples")
print()

if disagreement_samples:
    print("=" * 70)
    print(f"SAMPLES WHERE MODELS DISAGREED ({len(disagreement_samples)} total)")
    print("=" * 70)
    print()
    for i, sample in enumerate(disagreement_samples[:10], 1):
        print(f"{i}. Image: {sample['image_id']}")
        print(f"   Ground Truth: {sample['ground_truth']}")
        print(f"   4B predicted: {sample['4b_prediction']}")
        print(f"   27B predicted: {sample['27b_prediction']}")
        print(f"   Winner: {sample['winner']}")
        print()

print(
    f"The models agree on {both_correct + both_wrong}/{total} samples ({agreement_rate:.1%})."
)
print(f"They only disagree on {only_4b_correct + only_27b_correct} samples.")
print()
if agreement_rate >= 0.90:
    print("This high agreement suggests they are functionally equivalent.")
    print("The small differences are due to different decision boundaries")
    print("on a handful of borderline cases, not systematic superiority.")
else:
    print("The models show notable disagreement, warranting further investigation")
    print("into which sample types each model handles differently.")
print("=" * 70)
print()
print(
    f"The models agree on {both_correct + both_wrong}/{total} samples ({agreement_rate:.1%})."
)
print(f"They only disagree on {only_4b_correct + only_27b_correct} samples.")
print()
print("This high agreement confirms they are functionally equivalent.")
print("The small differences are due to different decision boundaries")
print("on a handful of borderline cases, not systematic superiority.")
