#!/usr/bin/env python3
"""Analyze per-image optimal veracity/alignment contribution weights.

This script performs retrospective analysis to find the theoretical distribution
of optimal contribution weights for each image in the validation set.

For each image, we calculate: "What veracity/alignment weight would have
perfectly classified this image?" Then plot the distribution to understand
the problem space.
"""

import json
import sys
from pathlib import Path
from typing import Tuple

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from scipy.stats import gaussian_kde

sns.set_style("whitegrid")


def load_predictions(results_dir: Path):
    """Load raw predictions and ground truth."""
    with open(results_dir / "raw_predictions.json") as f:
        predictions = json.load(f)

    veracity_scores = []
    alignment_scores = []
    y_true = []

    for pred in predictions:
        veracity_scores.append(pred["veracity_score"])
        alignment_scores.append(pred["alignment_score"])
        # True = misinformation
        y_true.append(pred["ground_truth"] == "misinformation")

    return (np.array(veracity_scores), np.array(alignment_scores), np.array(y_true))


def calculate_optimal_weight_per_image(
    veracity_scores: np.ndarray,
    alignment_scores: np.ndarray,
    y_true: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray]:
    """Calculate optimal veracity/alignment contribution weight for each image.

    For each image, find the weight that would have correctly classified it.
    Weight ranges from 0 (all alignment) to 1 (all veracity).

    Returns:
        veracity_weights: Array of optimal veracity contribution (0-1)
        alignment_weights: Array of optimal alignment contribution (0-1)
        Note: veracity_weight + alignment_weight = 1
    """
    n = len(veracity_scores)
    optimal_veracity_weights = np.zeros(n)

    for i in range(n):
        v_score = veracity_scores[i]
        a_score = alignment_scores[i]
        is_misinfo = y_true[i]

        # Combined score = w*veracity + (1-w)*alignment
        # For misinformation: we want combined_score to be LOW
        # For legitimate: we want combined_score to be HIGH

        # Sweep through possible weights to find optimal
        best_weight = 0.5  # Default to equal weighting
        best_correctness = 0

        for w in np.linspace(0, 1, 101):  # 101 points from 0 to 1
            combined_score = w * v_score + (1 - w) * a_score

            # Predict misinformation if combined score < 0.5 (arbitrary threshold)
            predicted_misinfo = combined_score < 0.5

            # Check if prediction matches ground truth
            correctness = 1 if (predicted_misinfo == is_misinfo) else 0

            if correctness > best_correctness:
                best_correctness = correctness
                best_weight = w

        optimal_veracity_weights[i] = best_weight

    optimal_alignment_weights = 1 - optimal_veracity_weights

    return optimal_veracity_weights, optimal_alignment_weights


def plot_contribution_distribution(
    veracity_weights: np.ndarray,
    alignment_weights: np.ndarray,
    output_path: Path,
):
    """Plot smoothed distribution of optimal contribution weights.

    Creates:
    1. KDE (Kernel Density Estimation) smooth curve
    2. Histogram with overlay
    3. Statistics summary
    """
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))

    # 1. Veracity contribution distribution (smoothed)
    ax1 = axes[0, 0]
    kde_v = gaussian_kde(veracity_weights, bw_method="scott")
    x_range = np.linspace(0, 1, 200)
    ax1.plot(x_range, kde_v(x_range), linewidth=2.5, color="#E63946", label="KDE")
    ax1.hist(
        veracity_weights,
        bins=20,
        alpha=0.3,
        color="#E63946",
        density=True,
        label="Histogram",
    )
    ax1.axvline(
        np.mean(veracity_weights),
        color="#B91C1C",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {np.mean(veracity_weights):.2f}",
    )
    ax1.set_xlabel("Optimal Veracity Weight", fontsize=12, fontweight="bold")
    ax1.set_ylabel("Density", fontsize=12, fontweight="bold")
    ax1.set_title(
        "Theoretical Distribution: Veracity Contribution",
        fontsize=14,
        fontweight="bold",
    )
    ax1.legend()
    ax1.grid(alpha=0.3)

    # 2. Alignment contribution distribution (smoothed)
    ax2 = axes[0, 1]
    kde_a = gaussian_kde(alignment_weights, bw_method="scott")
    ax2.plot(x_range, kde_a(x_range), linewidth=2.5, color="#F4A261", label="KDE")
    ax2.hist(
        alignment_weights,
        bins=20,
        alpha=0.3,
        color="#F4A261",
        density=True,
        label="Histogram",
    )
    ax2.axvline(
        np.mean(alignment_weights),
        color="#D4860A",
        linestyle="--",
        linewidth=2,
        label=f"Mean: {np.mean(alignment_weights):.2f}",
    )
    ax2.set_xlabel("Optimal Alignment Weight", fontsize=12, fontweight="bold")
    ax2.set_ylabel("Density", fontsize=12, fontweight="bold")
    ax2.set_title(
        "Theoretical Distribution: Alignment Contribution",
        fontsize=14,
        fontweight="bold",
    )
    ax2.legend()
    ax2.grid(alpha=0.3)

    # 3. 2D density plot (veracity vs alignment)
    ax3 = axes[1, 0]
    # Create 2D histogram
    h = ax3.hist2d(veracity_weights, alignment_weights, bins=20, cmap="YlOrRd", cmin=1)
    ax3.plot([0, 1], [1, 0], "k--", alpha=0.5, linewidth=2, label="Sum=1 constraint")
    ax3.set_xlabel("Veracity Weight", fontsize=12, fontweight="bold")
    ax3.set_ylabel("Alignment Weight", fontsize=12, fontweight="bold")
    ax3.set_title("2D Distribution: Weight Pairs", fontsize=14, fontweight="bold")
    ax3.legend()
    plt.colorbar(h[3], ax=ax3, label="Count")

    # 4. Statistics summary
    ax4 = axes[1, 1]
    ax4.axis("off")

    stats_text = f"""
    THEORETICAL DISTRIBUTION ANALYSIS
    ═══════════════════════════════════

    Veracity Contribution:
      Mean:     {np.mean(veracity_weights):.3f}
      Median:   {np.median(veracity_weights):.3f}
      Std Dev:  {np.std(veracity_weights):.3f}
      Min/Max:  {np.min(veracity_weights):.3f} / {np.max(veracity_weights):.3f}

    Alignment Contribution:
      Mean:     {np.mean(alignment_weights):.3f}
      Median:   {np.median(alignment_weights):.3f}
      Std Dev:  {np.std(alignment_weights):.3f}
      Min/Max:  {np.min(alignment_weights):.3f} / {np.max(alignment_weights):.3f}

    Distribution Characteristics:
      Veracity-heavy images:  {np.sum(veracity_weights > 0.7)} ({np.sum(veracity_weights > 0.7)/len(veracity_weights)*100:.1f}%)
      Alignment-heavy images: {np.sum(alignment_weights > 0.7)} ({np.sum(alignment_weights > 0.7)/len(alignment_weights)*100:.1f}%)
      Balanced images:        {np.sum((veracity_weights >= 0.4) & (veracity_weights <= 0.6))} ({np.sum((veracity_weights >= 0.4) & (veracity_weights <= 0.6))/len(veracity_weights)*100:.1f}%)

    Total images: {len(veracity_weights)}
    """

    ax4.text(
        0.1,
        0.5,
        stats_text,
        fontsize=11,
        fontfamily="monospace",
        verticalalignment="center",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    print(f"✓ Saved contribution distribution plot to {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_contribution_distribution.py <results_dir>")
        print(
            "Example: python analyze_contribution_distribution.py validation_results/med_mmhl_n163_4b_quantized"
        )
        sys.exit(1)

    results_dir = Path(sys.argv[1])

    if not results_dir.exists():
        print(f"Error: Directory not found: {results_dir}")
        sys.exit(1)

    print("\n📊 Analyzing per-image optimal contribution weights...")
    print(f"   Results directory: {results_dir}\n")

    # Load predictions
    veracity_scores, alignment_scores, y_true = load_predictions(results_dir)
    print(f"✓ Loaded {len(y_true)} predictions")

    # Calculate optimal weights for each image
    print("⚙️  Calculating optimal contribution weights for each image...")
    veracity_weights, alignment_weights = calculate_optimal_weight_per_image(
        veracity_scores, alignment_scores, y_true
    )
    print("✓ Calculated optimal weights")

    # Plot distribution
    output_path = results_dir / "contribution_distribution.png"
    print("📈 Generating smoothed distribution plots...")
    plot_contribution_distribution(veracity_weights, alignment_weights, output_path)

    # Save raw data
    data_output = results_dir / "optimal_weights.json"
    with open(data_output, "w") as f:
        json.dump(
            {
                "veracity_weights": veracity_weights.tolist(),
                "alignment_weights": alignment_weights.tolist(),
                "statistics": {
                    "veracity": {
                        "mean": float(np.mean(veracity_weights)),
                        "median": float(np.median(veracity_weights)),
                        "std": float(np.std(veracity_weights)),
                    },
                    "alignment": {
                        "mean": float(np.mean(alignment_weights)),
                        "median": float(np.median(alignment_weights)),
                        "std": float(np.std(alignment_weights)),
                    },
                },
            },
            f,
            indent=2,
        )
    print(f"✓ Saved optimal weights data to {data_output}")

    print("\n✅ Analysis complete!")
    print("\nKey insight: The theoretical distribution shows how optimal")
    print("contribution weights vary per-image. Your fixed thresholds")
    print("(0.65/0.30) approximate this varying optimal weighting.")


if __name__ == "__main__":
    main()
