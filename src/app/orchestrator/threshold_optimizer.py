"""
Threshold optimization for contextual authenticity scoring.

Performs grid search over veracity and alignment thresholds to find
optimal decision boundaries with bootstrap confidence intervals.
"""

import json
import logging
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from app.clinical.medgemma_client import get_medgemma_client
from app.orchestrator.langgraph_agent import MedContextLangGraphAgent

logger = logging.getLogger(__name__)


def compute_metrics(y_true: list[int], y_pred: list[int]) -> dict[str, float]:
    """Compute classification metrics."""
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    tn = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    accuracy = (tp + tn) / len(y_true) if len(y_true) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

    return {
        "accuracy": accuracy,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
    }


def apply_threshold_logic(
    veracity_scores: list[float],
    alignment_scores: list[float],
    veracity_threshold: float,
    alignment_threshold: float,
    logic: str,
) -> list[int]:
    """
    Apply threshold logic to scores.
    
    Returns binary predictions (1 = misinformation, 0 = legitimate).
    
    Logic options:
    - "OR": Flag if veracity < threshold OR alignment < threshold
    - "AND": Flag if veracity < threshold AND alignment < threshold
    - "MIN": Flag if min(veracity, alignment) < threshold
    """
    predictions = []
    for v, a in zip(veracity_scores, alignment_scores):
        if logic == "OR":
            pred = 1 if (v < veracity_threshold or a < alignment_threshold) else 0
        elif logic == "AND":
            pred = 1 if (v < veracity_threshold and a < alignment_threshold) else 0
        elif logic == "MIN":
            pred = 1 if min(v, a) < min(veracity_threshold, alignment_threshold) else 0
        else:
            raise ValueError(f"Unknown logic: {logic}")
        predictions.append(pred)
    return predictions


async def run_agent_on_dataset(dataset_path: str) -> dict[str, Any]:
    """
    Run MedContext agent on a dataset and extract raw scores.
    
    Returns dict with:
    - veracity_scores: list[float]
    - alignment_scores: list[float]
    - ground_truth: list[int] (1=misinformation, 0=legitimate)
    """
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    agent = MedContextLangGraphAgent()
    veracity_scores = []
    alignment_scores = []
    ground_truth = []

    logger.info(f"Running agent on {len(dataset)} samples for threshold optimization")

    for i, sample in enumerate(dataset):
        image_path = sample["image_path"]
        claim = sample["claim"]
        label = sample["label"]

        # Load image
        with open(image_path, "rb") as img_file:
            image_bytes = img_file.read()

        # Run agent
        try:
            state = agent.run(
                image_bytes=image_bytes,
                image_id=f"opt_{i}",
                context=claim,
                force_tools=[],
            )

            # Extract scores from triage
            triage = state.get("triage", {})
            veracity_score = triage.get("veracity_score", 0.5)
            alignment_score = triage.get("alignment_score", 0.5)

            veracity_scores.append(veracity_score)
            alignment_scores.append(alignment_score)
            ground_truth.append(1 if label.lower() == "misinformation" else 0)

            if (i + 1) % 10 == 0:
                logger.info(f"Processed {i + 1}/{len(dataset)} samples")

        except Exception as e:
            logger.warning(f"Failed to process sample {i}: {e}")
            continue

    return {
        "veracity_scores": veracity_scores,
        "alignment_scores": alignment_scores,
        "ground_truth": ground_truth,
    }


def grid_search_thresholds(
    veracity_scores: list[float],
    alignment_scores: list[float],
    ground_truth: list[int],
    threshold_range: list[float] | None = None,
) -> dict[str, Any]:
    """
    Grid search over threshold combinations.
    
    Returns dict with optimal thresholds and performance for each logic type.
    """
    if threshold_range is None:
        threshold_range = [i * 0.05 for i in range(21)]  # 0.0 to 1.0 in steps of 0.05

    logics = ["OR", "AND", "MIN"]
    all_results = []
    best_by_logic = {}

    for logic in logics:
        best_acc = 0.0
        best_config = None

        for v_thresh in threshold_range:
            for a_thresh in threshold_range:
                predictions = apply_threshold_logic(
                    veracity_scores,
                    alignment_scores,
                    v_thresh,
                    a_thresh,
                    logic,
                )
                metrics = compute_metrics(ground_truth, predictions)

                result = {
                    "logic": logic,
                    "veracity_threshold": v_thresh,
                    "alignment_threshold": a_thresh,
                    **metrics,
                }
                all_results.append(result)

                if metrics["accuracy"] > best_acc:
                    best_acc = metrics["accuracy"]
                    best_config = result

        best_by_logic[logic] = best_config

    # Find overall best
    overall_best = max(best_by_logic.values(), key=lambda x: x["accuracy"])

    return {
        "optimal": overall_best,
        "by_logic": best_by_logic,
        "all_results": all_results,
    }


def bootstrap_confidence_intervals(
    veracity_scores: list[float],
    alignment_scores: list[float],
    ground_truth: list[int],
    optimal_config: dict[str, Any],
    n_iterations: int = 1000,
) -> dict[str, dict[str, float]]:
    """
    Compute bootstrap confidence intervals for optimal configuration.
    """
    rng = np.random.default_rng(seed=42)
    n_samples = len(ground_truth)

    bootstrap_accuracies = []
    bootstrap_precisions = []
    bootstrap_recalls = []
    bootstrap_f1s = []

    for _ in range(n_iterations):
        # Resample with replacement
        indices = rng.choice(n_samples, size=n_samples, replace=True)
        boot_veracity = [veracity_scores[i] for i in indices]
        boot_alignment = [alignment_scores[i] for i in indices]
        boot_truth = [ground_truth[i] for i in indices]

        # Apply optimal thresholds
        predictions = apply_threshold_logic(
            boot_veracity,
            boot_alignment,
            optimal_config["veracity_threshold"],
            optimal_config["alignment_threshold"],
            optimal_config["logic"],
        )

        metrics = compute_metrics(boot_truth, predictions)
        bootstrap_accuracies.append(metrics["accuracy"])
        bootstrap_precisions.append(metrics["precision"])
        bootstrap_recalls.append(metrics["recall"])
        bootstrap_f1s.append(metrics["f1"])

    # Compute 95% CIs
    def compute_ci(values):
        return {
            "mean": float(np.mean(values)),
            "ci_lower": float(np.percentile(values, 2.5)),
            "ci_upper": float(np.percentile(values, 97.5)),
        }

    return {
        "accuracy": compute_ci(bootstrap_accuracies),
        "precision": compute_ci(bootstrap_precisions),
        "recall": compute_ci(bootstrap_recalls),
        "f1": compute_ci(bootstrap_f1s),
    }


async def optimize_thresholds_from_dataset(dataset_path: str) -> dict[str, Any]:
    """
    Full threshold optimization pipeline.
    
    1. Run agent on dataset to get raw scores
    2. Grid search for optimal thresholds
    3. Compute bootstrap confidence intervals
    
    Returns comprehensive results dict.
    """
    logger.info(f"Starting threshold optimization for dataset: {dataset_path}")

    # Step 1: Run agent
    agent_results = await run_agent_on_dataset(dataset_path)

    # Step 2: Grid search
    search_results = grid_search_thresholds(
        agent_results["veracity_scores"],
        agent_results["alignment_scores"],
        agent_results["ground_truth"],
    )

    # Step 3: Bootstrap CIs
    bootstrap_ci = bootstrap_confidence_intervals(
        agent_results["veracity_scores"],
        agent_results["alignment_scores"],
        agent_results["ground_truth"],
        search_results["optimal"],
    )

    logger.info(
        f"Optimization complete. Optimal: {search_results['optimal']['logic']} "
        f"v<{search_results['optimal']['veracity_threshold']:.2f} / "
        f"a<{search_results['optimal']['alignment_threshold']:.2f} → "
        f"Acc={search_results['optimal']['accuracy']:.3f}"
    )

    return {
        "optimal": search_results["optimal"],
        "bootstrap_ci": bootstrap_ci,
        "by_logic": search_results["by_logic"],
        "n_samples": len(agent_results["ground_truth"]),
    }
