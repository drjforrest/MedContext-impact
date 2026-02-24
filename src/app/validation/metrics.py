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


def compute_three_dimensional_metrics(
    predictions: List[Dict[str, Any]],
    ground_truth: List[Dict[str, Any]],
    suppress_warnings: bool = False,
) -> Dict[str, Any]:
    """Compute metrics for each MedContext dimension.

    Dimensions:
    - pixel_authenticity: fraction marked authentic
    - veracity: claim plausibility (binary: is_fake_claim)
    - alignment: image-claim consistency (binary: expected_misalignment)

    Predictions should have: pixel_authentic, claim_veracity (or veracity_score),
    alignment (or alignment_score).
    Ground truth should have: is_fake_claim, expected_misalignment.

    Args:
        predictions: List of prediction dictionaries
        ground_truth: List of ground truth dictionaries
        suppress_warnings: If True, suppress sample size warnings (useful for bootstrap iterations)
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("predictions and ground_truth must have same length")
    if len(predictions) == 0:
        raise ValueError("predictions and ground_truth cannot be empty")

    # Warn if sample size is small (but allow suppression during bootstrap)
    if not suppress_warnings and len(predictions) < 30:
        warnings.warn(
            f"Sample size n={len(predictions)} is insufficient for statistical validation. "
            "Metrics may be unreliable. Minimum recommended: n=30 for basic validation, "
            "n=100+ for publication-quality results.",
            UserWarning,
            stacklevel=2,
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
        not g.get("is_misinformation", g.get("is_fake_claim", False))
        for g in ground_truth
    ]  # not misinformation = plausible

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
    # expected_misalignment=True means misaligned, False means aligned
    alignment_score = [
        p.get("alignment_score", p.get("alignment", 0.5)) for p in predictions
    ]
    if isinstance(alignment_score[0], bool):
        alignment_pred = alignment_score
    else:
        alignment_pred = [
            s > 0.5 for s in alignment_score
        ]  # high = aligned = not misaligned

    # Handle both key formats: "alignment" string or "expected_misalignment" boolean
    alignment_truth = []
    for g in ground_truth:
        if "expected_misalignment" in g:
            # expected_misalignment=True means misaligned, so aligned = not expected_misalignment
            alignment_truth.append(not g["expected_misalignment"])
        else:
            # Fall back to alignment string key
            alignment_truth.append(
                g.get("alignment", "").lower() in ("aligned", "aligns_fully")
            )

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


# VERACITY_FIRST thresholds (from validation methodology: 5-fold CV optimized)
VERACITY_THRESHOLD = 0.65
ALIGNMENT_THRESHOLD = 0.30


def _apply_veracity_first(
    veracity_score: float,
    alignment_score: float,
    v_thresh: float = VERACITY_THRESHOLD,
    a_thresh: float = ALIGNMENT_THRESHOLD,
) -> bool:
    """Apply VERACITY_FIRST rule: misinformation if veracity < v_thresh OR alignment < a_thresh."""
    return veracity_score < v_thresh or alignment_score < a_thresh


def compute_misinformation_metrics(
    predictions: list[dict],
    ground_truth: list[dict],
    veracity_threshold: float = VERACITY_THRESHOLD,
    alignment_threshold: float = ALIGNMENT_THRESHOLD,
) -> dict[str, Any]:
    """Compute end-to-end misinformation detection metrics.

    Applies VERACITY_FIRST rule to veracity and alignment scores to produce
    binary Misinformation/Legitimate predictions, then evaluates against
    ground-truth is_misinformation labels.

    Returns:
        Dict with accuracy, precision, recall, f1, roc_auc (where applicable), n.
    """
    if len(predictions) != len(ground_truth):
        raise ValueError("predictions and ground_truth must have same length")
    if len(predictions) == 0:
        raise ValueError("predictions and ground_truth cannot be empty")

    y_true = [g.get("is_misinformation", g.get("is_fake_claim", False)) for g in ground_truth]
    y_pred = [
        _apply_veracity_first(
            p.get("veracity_score", 0.5),
            p.get("alignment_score", 0.5),
            veracity_threshold,
            alignment_threshold,
        )
        for p in predictions
    ]

    # Continuous score for AUC: higher = more likely misinformation
    # 1 - min(v,a) approximates OR logic (either low => high score)
    y_score = [
        1.0 - min(p.get("veracity_score", 0.5), p.get("alignment_score", 0.5))
        for p in predictions
    ]

    acc = float(accuracy_score(y_true, y_pred))
    pr, re, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="binary", zero_division=np.nan
    )
    try:
        auc = float(roc_auc_score(y_true, y_score))
    except ValueError:
        auc = np.nan

    def nan_to_none(val: float) -> float | None:
        return None if np.isnan(val) else float(val)

    return {
        "accuracy": acc,
        "precision": nan_to_none(pr),
        "recall": nan_to_none(re),
        "f1": nan_to_none(f1),
        "roc_auc": nan_to_none(auc),
        "n": len(predictions),
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
        m = compute_three_dimensional_metrics(pred_sub, gt_sub, suppress_warnings=True)
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
