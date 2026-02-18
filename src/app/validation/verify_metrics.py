#!/usr/bin/env python3
"""Verify metrics in SUBMISSION.md match actual predictions.

This script recomputes all metrics from raw predictions and verifies they match
what's documented in SUBMISSION.md.
"""

import json
import sys
from pathlib import Path

from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# Expected values from SUBMISSION.md
EXPECTED_METRICS = {
    "pixel_forensics": {
        "accuracy": 0.479,
        "precision": 0.752,
        "recall": 0.559,
        "f1": 0.641,
    },
    "veracity": {"accuracy": 0.908, "precision": 0.984, "recall": 0.904, "f1": 0.943},
    "alignment": {"accuracy": 0.865, "precision": 0.885, "recall": 0.963, "f1": 0.923},
    "combined": {"accuracy": 0.883, "precision": 0.887, "recall": 0.985, "f1": 0.934},
}

TOLERANCE = 0.002  # Allow 0.2% difference for rounding


def verify_metrics():
    """Load predictions and verify metrics match SUBMISSION.md."""

    # Load predictions
    pred_file = (
        Path("validation_results") / "med_mmhl_n163_hf_27b" / "raw_predictions.json"
    )
    if not pred_file.exists():
        print(f"ERROR: Predictions file not found: {pred_file}")
        return False

    with open(pred_file, "r") as f:
        predictions = json.load(f)

    print(f"Loaded {len(predictions)} predictions")

    # Ground truth
    y_true = [p["ground_truth"]["is_misinformation"] for p in predictions]
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos

    print(
        f"Dataset: {len(y_true)} samples ({n_pos} misinformation, {n_neg} legitimate)"
    )

    if n_pos != 136 or n_neg != 27:
        print(
            f"ERROR: Expected 136 misinformation and 27 legitimate, got {n_pos} and {n_neg}"
        )
        return False

    all_pass = True

    # Verify each method
    methods = {
        "pixel_forensics": lambda p: (
            0 if p["predictions"]["pixel_forensics"]["pixel_authentic"] else 1
        ),
        "veracity": lambda p: (
            0
            if p["predictions"]["contextual_analysis"]["veracity_category"] == "true"
            else 1
        ),
        "alignment": lambda p: (
            0
            if p["predictions"]["contextual_analysis"]["alignment_category"]
            == "aligns_fully"
            else 1
        ),
        "combined": lambda p: (
            1 if p["predictions"]["combined_analysis"]["is_misleading"] else 0
        ),
    }

    for method_name, pred_fn in methods.items():
        print(f"\n{'=' * 60}")
        print(f"{method_name.upper().replace('_', ' ')}")
        print(f"{'=' * 60}")

        # Get predictions
        y_pred = [pred_fn(p) for p in predictions]

        # Compute metrics
        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        # Get confusion matrix
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()

        print(f"Confusion Matrix: TP={tp}, FP={fp}, TN={tn}, FN={fn}")
        print("Computed Metrics:")
        print(f"  Accuracy:  {acc:.1%}")
        print(f"  Precision: {prec:.1%}")
        print(f"  Recall:    {rec:.1%}")
        print(f"  F1 Score:  {f1:.3f}")

        # Verify against expected
        expected = EXPECTED_METRICS[method_name]
        print("\nExpected (from SUBMISSION.md):")
        print(f"  Accuracy:  {expected['accuracy']:.1%}")
        print(f"  Precision: {expected['precision']:.1%}")
        print(f"  Recall:    {expected['recall']:.1%}")
        print(f"  F1 Score:  {expected['f1']:.3f}")

        # Check if within tolerance
        checks = {
            "accuracy": abs(acc - expected["accuracy"]) <= TOLERANCE,
            "precision": abs(prec - expected["precision"]) <= TOLERANCE,
            "recall": abs(rec - expected["recall"]) <= TOLERANCE,
            "f1": abs(f1 - expected["f1"]) <= TOLERANCE,
        }

        if all(checks.values()):
            print(f"\n✅ PASS - All metrics match within {TOLERANCE:.1%} tolerance")
        else:
            print("\n❌ FAIL - Metrics don't match:")
            for metric, passed in checks.items():
                if not passed:
                    computed = {
                        "accuracy": acc,
                        "precision": prec,
                        "recall": rec,
                        "f1": f1,
                    }[metric]
                    diff = computed - expected[metric]
                    print(
                        f"  {metric}: computed={computed:.3f}, expected={expected[metric]:.3f}, diff={diff:+.3f}"
                    )
            all_pass = False

    print(f"\n{'=' * 60}")
    if all_pass:
        print("✅ ALL METHODS VERIFIED - SUBMISSION.md metrics are correct")
    else:
        print("❌ VERIFICATION FAILED - SUBMISSION.md metrics need updating")
    print(f"{'=' * 60}\n")

    return all_pass


if __name__ == "__main__":
    success = verify_metrics()
    sys.exit(0 if success else 1)
