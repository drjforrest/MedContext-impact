#!/usr/bin/env python3
"""Statistical significance test for model comparison."""

import json
from pathlib import Path

import numpy as np
from scipy import stats

# Load results
phase1_path = Path("validation_results/med_mmhl_n163_quantized_4b/chart_data.json")
phase2_path = Path("validation_results/med_mmhl_n163_hf_27b/chart_data.json")

with open(phase1_path) as f:
    phase1 = json.load(f)
with open(phase2_path) as f:
    phase2 = json.load(f)

# Extract metrics
metrics1 = phase1["raw_metrics"]
metrics2 = phase2["raw_metrics"]
n = metrics1["tp"] + metrics1["fp"] + metrics1["tn"] + metrics1["fn"]
acc1 = metrics1["accuracy"]
acc2 = metrics2["accuracy"]


# Calculate 95% confidence intervals using Wilson score interval
def wilson_ci(p, n, confidence=0.95):
    """Wilson score confidence interval for binomial proportion."""
    z = stats.norm.ppf((1 + confidence) / 2)
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt((p * (1 - p) / n + z**2 / (4 * n**2))) / denominator
    return center - margin, center + margin


ci1_lower, ci1_upper = wilson_ci(acc1, n)
ci2_lower, ci2_upper = wilson_ci(acc2, n)

# Extract confusion matrix components for aggregate statistics
tp1, fp1, tn1, fn1 = (
    phase1["raw_metrics"]["tp"],
    phase1["raw_metrics"]["fp"],
    phase1["raw_metrics"]["tn"],
    phase1["raw_metrics"]["fn"],
)
tp2, fp2, tn2, fn2 = (
    phase2["raw_metrics"]["tp"],
    phase2["raw_metrics"]["fp"],
    phase2["raw_metrics"]["tn"],
    phase2["raw_metrics"]["fn"],
)

# Calculate correct counts for each model
correct1 = tp1 + tn1  # 145
correct2 = tp2 + tn2  # 144

# Difference in correct predictions
diff = correct1 - correct2  # Should be 1

# Two-proportion z-test for independent proportions
# Note: This is a non-paired test suitable for aggregate counts
# A paired test (McNemar) would require per-sample predictions
p1 = correct1 / n
p2 = correct2 / n
p_pooled = (correct1 + correct2) / (2 * n)
se = np.sqrt(2 * p_pooled * (1 - p_pooled) / n)
z_stat = (p1 - p2) / se if se > 0 else 0
p_value = 2 * (1 - stats.norm.cdf(abs(z_stat)))  # Two-tailed test

print("=" * 70)
print("STATISTICAL SIGNIFICANCE TEST")
print("=" * 70)
print()
print("Sample Size: n = 163")
print()
print("Model 1 (Quantized 4B):")
print(f"  Accuracy: {acc1:.1%} ({correct1}/163)")
print(f"  95% CI: [{ci1_lower:.1%}, {ci1_upper:.1%}]")
print()
print("Model 2 (HuggingFace 27B):")
print(f"  Accuracy: {acc2:.1%} ({correct2}/{n})")
print(f"  95% CI: [{ci2_lower:.1%}, {ci2_upper:.1%}]")
print()

# Compute dynamic interpretation values
diff_pp = (acc1 - acc2) * 100  # Percentage-point difference
ci1_margin = (ci1_upper - ci1_lower) / 2 * 100  # CI margin for model 1 in pp
ci2_margin = (ci2_upper - ci2_lower) / 2 * 100  # CI margin for model 2 in pp
avg_ci_margin = (ci1_margin + ci2_margin) / 2  # Average CI margin
ci_overlap = ci1_upper >= ci2_lower and ci2_upper >= ci1_lower  # Boolean for overlap

print("Comparison:")
print(f"  Difference: {acc1 - acc2:.1%} ({diff} sample{'s' if abs(diff) != 1 else ''})")
print(f"  Overlap in CIs: {'YES' if ci_overlap else 'NO'}")
print(f"  Two-proportion z-test p-value: {p_value:.3f}")
print("  Note: Using non-paired test (paired test requires per-sample predictions)")
print()

print("=" * 70)
print("INTERPRETATION")
print("=" * 70)
print()

if p_value > 0.05:
    print("✅ NOT STATISTICALLY SIGNIFICANT (p > 0.05)")
    print()
    print(f"The {diff_pp:.1f}pp difference is well within random variation.")
    print(
        f"With n={n}, confidence intervals are ±{avg_ci_margin:.1f} percentage points."
    )
    print()
    print("Conclusion: The models perform equivalently.")
    print(
        f"The difference of {diff} sample{'s' if abs(diff) != 1 else ''} could easily flip with a different"
    )
    print("random seed or subset selection.")
else:
    print("❌ STATISTICALLY SIGNIFICANT (p < 0.05)")
    print()
    print("The difference is unlikely due to chance alone.")

print()
print("=" * 70)
print("WHAT IF WE USED A DIFFERENT RANDOM SEED?")
print("=" * 70)
print()
print(f"With {n} samples from 1,785 total:")
print("  - Many possible subsets")
print("  - Each subset will have different difficulty")
print(f"  - Results could easily vary by ±{avg_ci_margin:.0f} percentage points")
print()
print("Example: If the random subset had more challenging cases,")
print("both models might score 85-87%. If easier cases, 90-92%.")
print()
print(f"The {diff_pp:.1f}pp difference ({diff} sample{'s' if abs(diff) != 1 else ''}) is MUCH smaller than the")
print(f"expected variation from different random subsets (~{avg_ci_margin:.0f}pp).")
print()
print("=" * 70)
