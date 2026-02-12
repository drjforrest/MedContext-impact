"""Metrics for validation studies."""

from __future__ import annotations

import warnings
from typing import Any, Dict, List

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_recall_fscore_support,
    roc_auc_score,
)
from sklearn.utils import resample


def compute_three_dimensional_metrics(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Compute metrics for each MedContext dimension.

    Dimensions:
    - pixel_authenticity: fraction marked authentic
    - veracity: claim plausibility (binary: is_fake_claim)
    - alignment: image-claim consistency (binary: expected_misalignment)

    Predictions should have: pixel_authentic, claim_veracity (or veracity_score),
    alignment (or alignment_score).
    Ground truth should have: is_fake_claim, expected_misalignment.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("predictions and ground_truth must have same length")
    if len(predictions) == 0:
        raise ValueError("predictions and ground_truth cannot be empty")

    # Warn if sample size is small
    if len(predictions) < 30:
        warnings.warn(
            f"Sample size n={len(predictions)} is insufficient for statistical validation. "
            "Metrics may be unreliable. Minimum recommended: n=30 for basic validation, "
            "n=100+ for publication-quality results.",
            UserWarning
        )

    # Dimension 1: Pixel authenticity (rate, not classification)
    pixel_authentic = [p.get("pixel_authentic", True) for p in predictions]
    pixel_rate = np.mean(pixel_authentic)

    # Dimension 2: Veracity
    # In Med-MMHL: is_fake_claim=True means misinformation
    # Our model: high veracity_score = plausible
    veracity_score = [
        p.get("veracity_score", p.get("claim_veracity", 0.5)) for p in predictions
    ]
    veracity_pred = [
        s > 0.5 for s in veracity_score
    ]  # high score = plausible = not fake
    veracity_truth = [
        not g["is_fake_claim"] for g in ground_truth
    ]  # not fake = plausible

    veracity_acc = accuracy_score(veracity_truth, veracity_pred)
    veracity_pr, veracity_re, veracity_f1, _ = precision_recall_fscore_support(
        veracity_truth, veracity_pred, average="binary", zero_division=np.nan
    )
    try:
        veracity_auc = roc_auc_score(
            veracity_truth,
            [p.get("veracity_score", 0.5) for p in predictions],
        )
    except ValueError:
        # ROC AUC undefined when only one class present
        veracity_auc = np.nan

    # Dimension 3: Alignment
    # expected_misalignment=True means fake (misaligned)
    alignment_score = [
        p.get("alignment_score", p.get("alignment", 0.5)) for p in predictions
    ]
    if isinstance(alignment_score[0], bool):
        alignment_pred = alignment_score
    else:
        alignment_pred = [
            s > 0.5 for s in alignment_score
        ]  # high = aligned = not misaligned
    alignment_truth = [
        not g["expected_misalignment"] for g in ground_truth
    ]  # not misaligned = aligned

    alignment_acc = accuracy_score(alignment_truth, alignment_pred)
    alignment_pr, alignment_re, alignment_f1, _ = precision_recall_fscore_support(
        alignment_truth, alignment_pred, average="binary", zero_division=np.nan
    )
    try:
        alignment_auc = roc_auc_score(
            alignment_truth,
            [p.get("alignment_score", 0.5) for p in predictions],
        )
    except ValueError:
        # ROC AUC undefined when only one class present
        alignment_auc = np.nan

    # Convert NaN to None for JSON serialization
    def nan_to_none(val: float) -> float | None:
        return None if np.isnan(val) else float(val)

    return {
        "pixel_authenticity": {
            "mean_authentic_rate": float(pixel_rate),
            "n": len(predictions),
        },
        "veracity": {
            "accuracy": float(veracity_acc),
            "precision": nan_to_none(veracity_pr),
            "recall": nan_to_none(veracity_re),
            "f1": nan_to_none(veracity_f1),
            "roc_auc": nan_to_none(veracity_auc),
            "n": len(predictions),
        },
        "alignment": {
            "accuracy": float(alignment_acc),
            "precision": nan_to_none(alignment_pr),
            "recall": nan_to_none(alignment_re),
            "f1": nan_to_none(alignment_f1),
            "roc_auc": nan_to_none(alignment_auc),
            "n": len(predictions),
        },
    }


def bootstrap_confidence_intervals(
    predictions: List[Dict],
    ground_truth: List[Dict],
    n_iterations: int = 1000,
    random_state: int = 42,
) -> Dict[str, Dict[str, float]]:
    """Bootstrap 95% confidence intervals for veracity and alignment metrics."""
    n = len(predictions)
    rng = np.random.RandomState(random_state)

    veracity_acc_samples = []
    alignment_acc_samples = []
    veracity_f1_samples = []
    alignment_f1_samples = []

    for i in range(n_iterations):
        idx = rng.randint(0, n, size=n)
        pred_sub = [predictions[j] for j in idx]
        gt_sub = [ground_truth[j] for j in idx]
        m = compute_three_dimensional_metrics(pred_sub, gt_sub)
        veracity_acc_samples.append(m["veracity"]["accuracy"])
        alignment_acc_samples.append(m["alignment"]["accuracy"])
        veracity_f1_samples.append(m["veracity"]["f1"])
        alignment_f1_samples.append(m["alignment"]["f1"])

    def ci(values: List[float]) -> Dict[str, float]:
        arr = np.array(values)
        return {
            "mean": float(np.mean(arr)),
            "ci_lower": float(np.percentile(arr, 2.5)),
            "ci_upper": float(np.percentile(arr, 97.5)),
            "std": float(np.std(arr)),
        }

    return {
        "veracity_accuracy": ci(veracity_acc_samples),
        "veracity_f1": ci(veracity_f1_samples),
        "alignment_accuracy": ci(alignment_acc_samples),
        "alignment_f1": ci(alignment_f1_samples),
    }
