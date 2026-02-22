#!/usr/bin/env python3
"""[DEPRECATED] Compare 3 MedGemma variants side-by-side.

**NOTE:** This script is no longer part of the primary thesis. The current focus
is on demonstrating that hierarchical optimization of contextual signals (veracity
+ alignment) achieves strong performance with Q4_KM quantized model—NOT on comparing
model variants.

Legacy script kept for historical reference only.

Original usage:
  uv run python -m app.validation.compare_variants

  # Custom directories:
  uv run python -m app.validation.compare_variants \
    --it validation_results/med_mmhl_n163_4b_it \
    --pt validation_results/med_mmhl_n163_4b_pt \
    --q  validation_results/med_mmhl_n163_4b_quantized

  # Skip missing variants:
  uv run python -m app.validation.compare_variants --skip-missing
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)

from app.validation import optimize_thresholds_cv as _cv_module


def load_predictions(results_dir: Path) -> list[dict]:
    """Load raw_predictions.json from a results directory."""
    raw_path = results_dir / "raw_predictions.json"
    if not raw_path.exists():
        raise FileNotFoundError(f"No raw_predictions.json in {results_dir}")
    with open(raw_path, encoding="utf-8") as f:
        return json.load(f)


def load_report(results_dir: Path) -> dict:
    """Load validation_report.json if it exists."""
    report_path = results_dir / "validation_report.json"
    if report_path.exists():
        with open(report_path, encoding="utf-8") as f:
            return json.load(f)
    return {}


def extract_scores(
    predictions: list[dict],
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Extract veracity scores, alignment scores, and ground truth labels."""
    veracity_scores = []
    alignment_scores = []
    y_true = []

    for pred in predictions:
        context = pred["predictions"].get("contextual_analysis", {})
        veracity_scores.append(context.get("veracity_score", 0.5))
        alignment_scores.append(context.get("alignment_score", 0.5))
        gt = pred.get("ground_truth", {})
        y_true.append(gt.get("is_misinformation", False))

    return np.array(veracity_scores), np.array(alignment_scores), np.array(y_true)


def compute_default_metrics(predictions: list[dict]) -> dict:
    """Compute metrics using default thresholds (VERACITY_FIRST logic)."""
    y_true = []
    y_pred = []

    for pred in predictions:
        gt = pred["ground_truth"].get("is_misinformation", False)
        combined = pred["predictions"].get("combined_analysis", {})
        pred_misinfo = combined.get("is_misinformation", False)
        y_true.append(gt)
        y_pred.append(pred_misinfo)

    y_true_arr = np.array(y_true)
    y_pred_arr = np.array(y_pred)

    return {
        "accuracy": float(accuracy_score(y_true_arr, y_pred_arr)),
        "precision": float(precision_score(y_true_arr, y_pred_arr, zero_division=0)),
        "recall": float(recall_score(y_true_arr, y_pred_arr, zero_division=0)),
        "f1": float(f1_score(y_true_arr, y_pred_arr, zero_division=0)),
        "n": len(predictions),
    }


def compute_optimized_metrics(
    veracity_scores: np.ndarray,
    alignment_scores: np.ndarray,
    y_true: np.ndarray,
    cv_module,
) -> dict:
    """Run 5-fold CV threshold optimization and return metrics."""
    try:
        cv_result = cv_module.cross_validate_thresholds(
            veracity_scores,
            alignment_scores,
            y_true,
            logic="OR",
            n_folds=5,
            seed=42,
        )
        return {
            "mean_veracity_threshold": float(
                cv_result["recommended_thresholds"]["veracity_threshold"]
            ),
            "mean_alignment_threshold": float(
                cv_result["recommended_thresholds"]["alignment_threshold"]
            ),
            "cv_accuracy": float(cv_result["mean_val_metrics"]["accuracy"]),
            "cv_precision": float(cv_result["mean_val_metrics"]["precision"]),
            "cv_recall": float(cv_result["mean_val_metrics"]["recall"]),
            "cv_f1": float(cv_result["mean_val_metrics"]["f1"]),
        }
    except Exception as e:
        return {"error": str(e)}


def bootstrap_ci(
    veracity_scores: np.ndarray,
    alignment_scores: np.ndarray,
    y_true: np.ndarray,
    n_iterations: int = 1000,
    seed: int = 42,
) -> dict:
    """Bootstrap 95% CI for accuracy."""
    rng = np.random.RandomState(seed)
    n = len(y_true)
    accuracies = []

    for _ in range(n_iterations):
        idx = rng.randint(0, n, size=n)
        v = veracity_scores[idx]
        a = alignment_scores[idx]
        yt = y_true[idx]
        # Use combined VERACITY_FIRST logic
        y_pred = []
        for vi, ai in zip(v, a):
            if vi < 0.5:
                y_pred.append(True)
            elif vi >= 0.8:
                y_pred.append(False)
            elif ai < 0.5:
                y_pred.append(True)
            elif ai >= 0.8:
                y_pred.append(False)
            else:
                y_pred.append(True)  # Conservative
        accuracies.append(accuracy_score(yt, y_pred))

    arr = np.array(accuracies)
    return {
        "mean": float(np.mean(arr)),
        "ci_lower": float(np.percentile(arr, 2.5)),
        "ci_upper": float(np.percentile(arr, 97.5)),
        "std": float(np.std(arr)),
    }


def print_comparison_table(variants: dict[str, dict]) -> None:
    """Print a formatted side-by-side comparison table."""
    print()
    print("=" * 80)
    print("MedGemma 3-Variant Comparison (Med-MMHL, n=163, seed=42)")
    print("=" * 80)

    # Header
    labels = list(variants.keys())
    header = f"{'Metric':<25}"
    for label in labels:
        header += f" {label:>16}"
    print(header)
    print("-" * 80)

    # Default threshold metrics
    print("Default Thresholds (VERACITY_FIRST):")
    for metric in ["accuracy", "precision", "recall", "f1"]:
        row = f"  {metric.capitalize():<23}"
        for label in labels:
            val = variants[label]["default_metrics"].get(metric)
            row += f" {val:>15.1%}" if val is not None else f" {'N/A':>15}"
        print(row)

    # Bootstrap CI
    print()
    print("Bootstrap 95% CI (Accuracy):")
    row_mean = f"  {'Mean':<23}"
    row_ci = f"  {'95% CI':<23}"
    for label in labels:
        ci = variants[label].get("bootstrap_ci", {})
        if "mean" in ci:
            row_mean += f" {ci['mean']:>15.1%}"
            row_ci += f" [{ci['ci_lower']:.1%},{ci['ci_upper']:.1%}]".rjust(16)
        else:
            row_mean += f" {'N/A':>15}"
            row_ci += f" {'N/A':>15}"
    print(row_mean)
    print(row_ci)

    # CV-optimized metrics
    print()
    print("CV-Optimized Thresholds (5-fold):")
    for metric in ["cv_accuracy", "cv_f1"]:
        display_name = metric.replace("cv_", "").capitalize()
        row = f"  {display_name:<23}"
        for label in labels:
            opt = variants[label].get("optimized_metrics", {})
            val = opt.get(metric)
            if val is not None:
                row += f" {val:>15.1%}"
            elif "error" in opt:
                row += f" {'error':>15}"
            else:
                row += f" {'N/A':>15}"
        print(row)

    # Optimal thresholds
    row_vt = f"  {'Veracity thresh':<23}"
    row_at = f"  {'Alignment thresh':<23}"
    for label in labels:
        opt = variants[label].get("optimized_metrics", {})
        vt = opt.get("mean_veracity_threshold")
        at = opt.get("mean_alignment_threshold")
        row_vt += f" {vt:>15.2f}" if vt is not None else f" {'N/A':>15}"
        row_at += f" {at:>15.2f}" if at is not None else f" {'N/A':>15}"
    print(row_vt)
    print(row_at)

    # Sample counts
    print()
    print("Sample Info:")
    row_n = f"  {'n samples':<23}"
    for label in labels:
        n = variants[label]["default_metrics"].get("n", 0)
        row_n += f" {n:>15}"
    print(row_n)

    # Model info
    print()
    print("Model Info:")
    for label in labels:
        report = variants[label].get("report", {})
        model_label = report.get("model_label", label)
        provider = report.get("medgemma_provider", "unknown")
        model = report.get("medgemma_model", "unknown")
        print(f"  {label}: {model_label} ({provider}: {model})")

    print("=" * 80)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Compare 3 MedGemma variants side-by-side"
    )
    parser.add_argument(
        "--it",
        type=Path,
        default=Path("validation_results/med_mmhl_n163_4b_it"),
        help="IT variant results directory",
    )
    parser.add_argument(
        "--pt",
        type=Path,
        default=Path("validation_results/med_mmhl_n163_4b_pt"),
        help="PT variant results directory",
    )
    parser.add_argument(
        "--q",
        type=Path,
        default=Path("validation_results/med_mmhl_n163_4b_quantized"),
        help="Q (quantized) variant results directory",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation_results/three_variant_comparison.json"),
        help="Output comparison JSON file",
    )
    parser.add_argument(
        "--skip-missing",
        action="store_true",
        help="Skip variants with missing results instead of erroring",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=1000,
        help="Bootstrap iterations for CI (default: 1000, 0=disable)",
    )
    args = parser.parse_args()

    cv_mod = _cv_module

    variant_dirs = {
        "IT": args.it,
        "PT": args.pt,
        "Q": args.q,
    }

    variants = {}

    for label, results_dir in variant_dirs.items():
        print(f"Loading {label} variant from {results_dir}...")
        if (
            not results_dir.exists()
            or not (results_dir / "raw_predictions.json").exists()
        ):
            if args.skip_missing:
                print(f"  SKIPPED: {results_dir} not found")
                continue
            else:
                print(f"  ERROR: {results_dir} not found. Use --skip-missing to skip.")
                return 1

        predictions = load_predictions(results_dir)
        report = load_report(results_dir)
        v_scores, a_scores, y_true = extract_scores(predictions)

        variant_data = {
            "results_dir": str(results_dir),
            "report": report,
            "default_metrics": compute_default_metrics(predictions),
        }

        # Bootstrap CI
        if args.bootstrap > 0:
            print(f"  Computing bootstrap CI ({args.bootstrap} iterations)...")
            variant_data["bootstrap_ci"] = bootstrap_ci(
                v_scores,
                a_scores,
                y_true,
                n_iterations=args.bootstrap,
            )

        # CV-optimized thresholds
        if cv_mod is not None:
            print("  Running 5-fold CV threshold optimization...")
            variant_data["optimized_metrics"] = compute_optimized_metrics(
                v_scores,
                a_scores,
                y_true,
                cv_mod,
            )

        variants[label] = variant_data
        print(
            f"  OK: n={len(predictions)}, acc={variant_data['default_metrics']['accuracy']:.1%}"
        )

    if not variants:
        print("Error: No variants loaded. Nothing to compare.")
        return 1

    # Print comparison table
    print_comparison_table(variants)

    # Save comparison JSON
    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Make numpy types JSON-serializable
    comparison = {
        "variants": {
            label: {
                k: v
                for k, v in data.items()
                if k != "report"  # exclude full report to keep output concise
            }
            for label, data in variants.items()
        },
        "metadata": {
            "n_variants": len(variants),
            "variant_labels": list(variants.keys()),
            "bootstrap_iterations": args.bootstrap,
        },
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2, default=str)

    print(f"\nComparison saved to {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
