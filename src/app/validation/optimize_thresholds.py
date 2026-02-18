#!/usr/bin/env python3
"""Optimize decision thresholds and compute bootstrap confidence intervals.

This script:
1. Loads raw predictions from validation results
2. Sweeps through different threshold combinations
3. Finds optimal thresholds that maximize accuracy/F1
4. Computes bootstrap confidence intervals
5. Generates threshold sensitivity plots
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

sns.set_style("whitegrid")


def load_predictions(results_dir: Path):
    """Load raw predictions."""
    with open(results_dir / "raw_predictions.json") as f:
        predictions = json.load(f)
    return predictions


def extract_scores_and_labels(predictions):
    """Extract veracity scores, alignment scores, and ground truth labels."""
    veracity_scores = []
    alignment_scores = []
    y_true = []

    for pred in predictions:
        # Get contextual analysis
        context = pred["predictions"].get("contextual_analysis", {})

        # Extract scores (default to 0.5 if missing)
        veracity_scores.append(context.get("veracity_score", 0.5))
        alignment_scores.append(context.get("alignment_score", 0.5))

        # Ground truth
        ground_truth = pred.get("ground_truth", {})
        if "is_misinformation" not in ground_truth:
            raise ValueError(
                f"Missing ground truth for prediction: {pred.get('id', 'unknown')}"
            )
        y_true.append(ground_truth["is_misinformation"])

    return np.array(veracity_scores), np.array(alignment_scores), np.array(y_true)


def apply_thresholds(
    veracity_scores,
    alignment_scores,
    veracity_threshold,
    alignment_threshold,
    logic="AND",
):
    """Apply thresholds to predict misinformation.

    Args:
        veracity_scores: Array of veracity scores (0-1)
        alignment_scores: Array of alignment scores (0-1)
        veracity_threshold: Threshold for veracity (predict misinformation if BELOW)
        alignment_threshold: Threshold for alignment (predict misinformation if BELOW)
        logic: "AND" (both must fail) or "OR" (either can fail) or "MIN" (use minimum score)

    Returns:
        Array of predictions (True = misinformation)
    """
    if logic == "AND":
        # Predict misinformation if BOTH veracity AND alignment are low
        return (veracity_scores < veracity_threshold) & (
            alignment_scores < alignment_threshold
        )
    elif logic == "OR":
        # Predict misinformation if EITHER veracity OR alignment is low
        return (veracity_scores < veracity_threshold) | (
            alignment_scores < alignment_threshold
        )
    elif logic == "MIN":
        # Use minimum score (most conservative signal)
        min_scores = np.minimum(veracity_scores, alignment_scores)
        threshold = (veracity_threshold + alignment_threshold) / 2  # Average threshold
        return min_scores < threshold
    else:
        raise ValueError(f"Unknown logic: {logic}")


def sweep_thresholds(veracity_scores, alignment_scores, y_true, logic="OR"):
    """Sweep through threshold combinations to find optimal."""
    # Sweep from 0.3 to 0.9 in steps of 0.05
    thresholds = np.arange(0.3, 0.95, 0.05)

    best_acc = 0
    best_f1 = 0
    best_config_acc = None
    best_config_f1 = None

    results = []

    for v_thresh in thresholds:
        for a_thresh in thresholds:
            y_pred = apply_thresholds(
                veracity_scores, alignment_scores, v_thresh, a_thresh, logic
            )

            acc = accuracy_score(y_true, y_pred)
            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            results.append(
                {
                    "veracity_threshold": v_thresh,
                    "alignment_threshold": a_thresh,
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1,
                }
            )

            if acc > best_acc:
                best_acc = acc
                best_config_acc = {
                    "veracity_threshold": v_thresh,
                    "alignment_threshold": a_thresh,
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1,
                }

            if f1 > best_f1:
                best_f1 = f1
                best_config_f1 = {
                    "veracity_threshold": v_thresh,
                    "alignment_threshold": a_thresh,
                    "accuracy": acc,
                    "precision": prec,
                    "recall": rec,
                    "f1": f1,
                }

    return results, best_config_acc, best_config_f1


def bootstrap_confidence_interval(
    veracity_scores,
    alignment_scores,
    y_true,
    veracity_threshold,
    alignment_threshold,
    logic="OR",
    n_iterations=1000,
):
    """Compute bootstrap confidence intervals for given thresholds."""
    n = len(y_true)
    accuracies = []
    precisions = []
    recalls = []
    f1s = []

    for _ in range(n_iterations):
        # Resample with replacement
        indices = np.random.choice(n, n, replace=True)

        v_boot = veracity_scores[indices]
        a_boot = alignment_scores[indices]
        y_boot = y_true[indices]

        # Apply thresholds
        y_pred = apply_thresholds(
            v_boot, a_boot, veracity_threshold, alignment_threshold, logic
        )

        # Compute metrics
        accuracies.append(accuracy_score(y_boot, y_pred))
        precisions.append(precision_score(y_boot, y_pred, zero_division=0))
        recalls.append(recall_score(y_boot, y_pred, zero_division=0))
        f1s.append(f1_score(y_boot, y_pred, zero_division=0))

    # Compute 95% CI
    return {
        "accuracy": {
            "mean": np.mean(accuracies),
            "ci_lower": np.percentile(accuracies, 2.5),
            "ci_upper": np.percentile(accuracies, 97.5),
        },
        "precision": {
            "mean": np.mean(precisions),
            "ci_lower": np.percentile(precisions, 2.5),
            "ci_upper": np.percentile(precisions, 97.5),
        },
        "recall": {
            "mean": np.mean(recalls),
            "ci_lower": np.percentile(recalls, 2.5),
            "ci_upper": np.percentile(recalls, 97.5),
        },
        "f1": {
            "mean": np.mean(f1s),
            "ci_lower": np.percentile(f1s, 2.5),
            "ci_upper": np.percentile(f1s, 97.5),
        },
    }


def plot_threshold_heatmap(results, metric="accuracy", output_path=None):
    """Generate heatmap showing metric across threshold combinations."""
    # Create grid
    thresholds = sorted(set(r["veracity_threshold"] for r in results))
    grid = np.zeros((len(thresholds), len(thresholds)))

    for i, v_thresh in enumerate(thresholds):
        for j, a_thresh in enumerate(thresholds):
            # Find result for this combination
            matching = [
                r
                for r in results
                if abs(r["veracity_threshold"] - v_thresh) < 0.01
                and abs(r["alignment_threshold"] - a_thresh) < 0.01
            ]
            if matching:
                grid[i, j] = matching[0][metric]

    plt.figure(figsize=(10, 8))

    # Compute dynamic color scale from data with padding
    data_min, data_max = grid.min(), grid.max()
    padding = (data_max - data_min) * 0.05  # 5% padding
    vmin = max(0, data_min - padding)  # Don't go below 0
    vmax = min(1.0, data_max + padding)  # Don't exceed 1.0 for metrics

    sns.heatmap(
        grid,
        xticklabels=[f"{t:.2f}" for t in thresholds],
        yticklabels=[f"{t:.2f}" for t in thresholds],
        annot=True,
        fmt=".3f",
        cmap="RdYlGn",
        vmin=vmin,
        vmax=vmax,
        cbar_kws={"label": metric.capitalize()},
    )
    plt.xlabel("Alignment Threshold", fontsize=12, fontweight="bold")
    plt.ylabel("Veracity Threshold", fontsize=12, fontweight="bold")
    plt.title(
        f"Threshold Sensitivity: {metric.capitalize()}", fontsize=14, fontweight="bold"
    )
    plt.tight_layout()

    if output_path:
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"✅ Generated: {output_path}")
    plt.close()


def main():
    if len(sys.argv) < 2:
        print("Usage: python optimize_thresholds.py <results_dir> [output_dir]")
        print()
        print("Example:")
        print(
            "  python scripts/optimize_thresholds.py validation_results/med_mmhl_n163_hf_27b"
        )
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    output_dir = (
        Path(sys.argv[2]) if len(sys.argv) > 2 else results_dir / "threshold_analysis"
    )
    output_dir.mkdir(exist_ok=True)

    print("=" * 70)
    print("THRESHOLD OPTIMIZATION & BOOTSTRAP CONFIDENCE INTERVALS")
    print("=" * 70)
    print()
    print(f"Loading predictions from: {results_dir}")

    predictions = load_predictions(results_dir)
    veracity_scores, alignment_scores, y_true = extract_scores_and_labels(predictions)

    print(f"Loaded {len(predictions)} samples")
    print(
        f"Ground truth: {sum(y_true)} misinformation, {len(y_true) - sum(y_true)} legitimate"
    )
    print()

    # Sweep thresholds for each logic type
    for logic in ["OR", "AND", "MIN"]:
        print(f"--- {logic} Logic ---")
        print("Sweeping thresholds...")

        results, best_acc, best_f1 = sweep_thresholds(
            veracity_scores, alignment_scores, y_true, logic
        )

        print("\nOptimal for Accuracy:")
        print(f"  Veracity threshold: {best_acc['veracity_threshold']:.2f}")
        print(f"  Alignment threshold: {best_acc['alignment_threshold']:.2f}")
        print(f"  Accuracy: {best_acc['accuracy']:.1%}")
        print(f"  Precision: {best_acc['precision']:.1%}")
        print(f"  Recall: {best_acc['recall']:.1%}")
        print(f"  F1: {best_acc['f1']:.3f}")

        print("\nOptimal for F1:")
        print(f"  Veracity threshold: {best_f1['veracity_threshold']:.2f}")
        print(f"  Alignment threshold: {best_f1['alignment_threshold']:.2f}")
        print(f"  Accuracy: {best_f1['accuracy']:.1%}")
        print(f"  Precision: {best_f1['precision']:.1%}")
        print(f"  Recall: {best_f1['recall']:.1%}")
        print(f"  F1: {best_f1['f1']:.3f}")

        # Bootstrap CI for optimal thresholds
        print("\nComputing bootstrap confidence intervals (1000 iterations)...")
        ci = bootstrap_confidence_interval(
            veracity_scores,
            alignment_scores,
            y_true,
            best_acc["veracity_threshold"],
            best_acc["alignment_threshold"],
            logic,
            n_iterations=1000,
        )

        print("\nBootstrap 95% CI (optimal for accuracy):")
        print(
            f"  Accuracy:  {ci['accuracy']['mean']:.1%} [{ci['accuracy']['ci_lower']:.1%}, {ci['accuracy']['ci_upper']:.1%}]"
        )
        print(
            f"  Precision: {ci['precision']['mean']:.1%} [{ci['precision']['ci_lower']:.1%}, {ci['precision']['ci_upper']:.1%}]"
        )
        print(
            f"  Recall:    {ci['recall']['mean']:.1%} [{ci['recall']['ci_lower']:.1%}, {ci['recall']['ci_upper']:.1%}]"
        )
        print(
            f"  F1:        {ci['f1']['mean']:.3f} [{ci['f1']['ci_lower']:.3f}, {ci['f1']['ci_upper']:.3f}]"
        )

        # Save results
        output_file = output_dir / f"threshold_optimization_{logic.lower()}.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "logic": logic,
                    "optimal_for_accuracy": best_acc,
                    "optimal_for_f1": best_f1,
                    "bootstrap_ci": ci,
                    "all_results": results,  # Save all results (complete grid)
                },
                f,
                indent=2,
            )

        print(f"\n✅ Saved: {output_file}")

        # Generate heatmap
        heatmap_path = output_dir / f"threshold_heatmap_{logic.lower()}_accuracy.png"
        plot_threshold_heatmap(results, "accuracy", heatmap_path)

        print()

    print("=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {output_dir}")
    print()
    print("Review threshold_optimization_*.json files to see:")
    print("  - Optimal thresholds for your current results")
    print("  - Bootstrap 95% confidence intervals")
    print("  - Sensitivity to threshold choices")


if __name__ == "__main__":
    main()
