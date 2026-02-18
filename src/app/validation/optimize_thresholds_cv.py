#!/usr/bin/env python3
"""Optimize decision thresholds with proper cross-validation to avoid test-set contamination.

This script implements a proper train/validation/test split:
1. Loads raw predictions from validation results
2. Splits data into train (60%), validation (20%), test (20%)
3. Performs grid search on TRAIN set only
4. Evaluates best thresholds on VALIDATION set
5. Reports final metrics on held-out TEST set
6. Optionally performs k-fold cross-validation for more robust threshold selection
"""

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import StratifiedKFold


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
    logic="OR",
):
    """Apply thresholds to predict misinformation.

    Args:
        veracity_scores: Array of veracity scores (0-1)
        alignment_scores: Array of alignment scores (0-1)
        veracity_threshold: Threshold for veracity (predict misinformation if BELOW)
        alignment_threshold: Threshold for alignment (predict misinformation if BELOW)
        logic: "OR" (either can fail) or "AND" (both must fail) or "MIN" (use minimum score)

    Returns:
        Array of predictions (True = misinformation)
    """
    if logic == "OR":
        # Predict misinformation if EITHER veracity OR alignment is low
        return (veracity_scores < veracity_threshold) | (
            alignment_scores < alignment_threshold
        )
    elif logic == "AND":
        # Predict misinformation if BOTH veracity AND alignment are low
        return (veracity_scores < veracity_threshold) & (
            alignment_scores < alignment_threshold
        )
    elif logic == "MIN":
        # Use minimum score (most conservative signal)
        min_scores = np.minimum(veracity_scores, alignment_scores)
        threshold = (veracity_threshold + alignment_threshold) / 2
        return min_scores < threshold
    else:
        raise ValueError(f"Unknown logic: {logic}")


def sweep_thresholds(
    veracity_scores, alignment_scores, y_true, logic="OR", metric="accuracy"
):
    """Sweep through threshold combinations to find optimal based on specified metric.

    Args:
        veracity_scores: Array of veracity scores
        alignment_scores: Array of alignment scores
        y_true: Ground truth labels
        logic: Decision logic ("OR", "AND", or "MIN")
        metric: Optimization metric ("accuracy" or "f1")

    Returns:
        Tuple of (all_results, best_config)
    """
    # Sweep from 0.3 to 0.9 in steps of 0.05
    thresholds = np.arange(0.3, 0.95, 0.05)

    best_score = 0
    best_config = None
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

            result = {
                "veracity_threshold": v_thresh,
                "alignment_threshold": a_thresh,
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1": f1,
            }
            results.append(result)

            # Update best based on optimization metric
            current_score = acc if metric == "accuracy" else f1
            if current_score > best_score:
                best_score = current_score
                best_config = result.copy()

    return results, best_config


def stratified_split(
    veracity_scores, alignment_scores, y_true, train_frac=0.6, val_frac=0.2, seed=42
):
    """Split data into train/val/test with stratification.

    Args:
        veracity_scores: Array of veracity scores
        alignment_scores: Array of alignment scores
        y_true: Ground truth labels
        train_frac: Fraction for training set (default 0.6)
        val_frac: Fraction for validation set (default 0.2)
        seed: Random seed for reproducibility

    Returns:
        Tuple of (train_data, val_data, test_data) where each is a dict with
        {veracity_scores, alignment_scores, y_true, indices}
    """
    np.random.seed(seed)
    n = len(y_true)
    indices = np.arange(n)

    # Stratified shuffle
    pos_indices = indices[y_true == 1]
    neg_indices = indices[y_true == 0]

    np.random.shuffle(pos_indices)
    np.random.shuffle(neg_indices)

    # Compute split sizes
    # n_train = int(n * train_frac)  # Unused but kept for documentation
    # n_val = int(n * val_frac)      # Unused but kept for documentation
    # n_test = n - n_train - n_val  # Remaining

    # Split positive and negative indices proportionally
    n_pos = len(pos_indices)
    n_neg = len(neg_indices)

    n_pos_train = int(n_pos * train_frac)
    n_pos_val = int(n_pos * val_frac)

    n_neg_train = int(n_neg * train_frac)
    n_neg_val = int(n_neg * val_frac)

    # Create splits
    train_indices = np.concatenate(
        [pos_indices[:n_pos_train], neg_indices[:n_neg_train]]
    )
    val_indices = np.concatenate(
        [
            pos_indices[n_pos_train : n_pos_train + n_pos_val],
            neg_indices[n_neg_train : n_neg_train + n_neg_val],
        ]
    )
    test_indices = np.concatenate(
        [pos_indices[n_pos_train + n_pos_val :], neg_indices[n_neg_train + n_neg_val :]]
    )

    # Shuffle each split
    np.random.shuffle(train_indices)
    np.random.shuffle(val_indices)
    np.random.shuffle(test_indices)

    def make_split(idxs):
        return {
            "veracity_scores": veracity_scores[idxs],
            "alignment_scores": alignment_scores[idxs],
            "y_true": y_true[idxs],
            "indices": idxs,
        }

    return make_split(train_indices), make_split(val_indices), make_split(test_indices)


def cross_validate_thresholds(
    veracity_scores, alignment_scores, y_true, logic="OR", n_folds=5, seed=42
):
    """Perform k-fold cross-validation to select optimal thresholds.

    Args:
        veracity_scores: Array of veracity scores
        alignment_scores: Array of alignment scores
        y_true: Ground truth labels
        logic: Decision logic
        n_folds: Number of CV folds
        seed: Random seed

    Returns:
        Dict with CV results and recommended thresholds
    """
    skf = StratifiedKFold(n_splits=n_folds, shuffle=True, random_state=seed)

    fold_results = []

    for fold_idx, (train_idx, val_idx) in enumerate(skf.split(veracity_scores, y_true)):
        # Split data
        v_train = veracity_scores[train_idx]
        a_train = alignment_scores[train_idx]
        y_train = y_true[train_idx]

        v_val = veracity_scores[val_idx]
        a_val = alignment_scores[val_idx]
        y_val = y_true[val_idx]

        # Find optimal thresholds on train set
        _, best_on_train = sweep_thresholds(
            v_train, a_train, y_train, logic, metric="accuracy"
        )

        # Evaluate on validation set
        v_thresh = best_on_train["veracity_threshold"]
        a_thresh = best_on_train["alignment_threshold"]

        y_pred_val = apply_thresholds(v_val, a_val, v_thresh, a_thresh, logic)

        val_metrics = {
            "accuracy": accuracy_score(y_val, y_pred_val),
            "precision": precision_score(y_val, y_pred_val, zero_division=0),
            "recall": recall_score(y_val, y_pred_val, zero_division=0),
            "f1": f1_score(y_val, y_pred_val, zero_division=0),
        }

        fold_results.append(
            {
                "fold": fold_idx + 1,
                "train_size": len(train_idx),
                "val_size": len(val_idx),
                "optimal_thresholds": {
                    "veracity_threshold": v_thresh,
                    "alignment_threshold": a_thresh,
                },
                "train_metrics": {
                    "accuracy": best_on_train["accuracy"],
                    "precision": best_on_train["precision"],
                    "recall": best_on_train["recall"],
                    "f1": best_on_train["f1"],
                },
                "val_metrics": val_metrics,
            }
        )

    # Aggregate results across folds
    mean_v_thresh = np.mean(
        [f["optimal_thresholds"]["veracity_threshold"] for f in fold_results]
    )
    mean_a_thresh = np.mean(
        [f["optimal_thresholds"]["alignment_threshold"] for f in fold_results]
    )

    mean_val_metrics = {
        metric: np.mean([f["val_metrics"][metric] for f in fold_results])
        for metric in ["accuracy", "precision", "recall", "f1"]
    }

    std_val_metrics = {
        metric: np.std([f["val_metrics"][metric] for f in fold_results])
        for metric in ["accuracy", "precision", "recall", "f1"]
    }

    return {
        "n_folds": n_folds,
        "fold_results": fold_results,
        "recommended_thresholds": {
            "veracity_threshold": float(mean_v_thresh),
            "alignment_threshold": float(mean_a_thresh),
        },
        "mean_val_metrics": mean_val_metrics,
        "std_val_metrics": std_val_metrics,
    }


def bootstrap_confidence_interval(
    veracity_scores,
    alignment_scores,
    y_true,
    veracity_threshold,
    alignment_threshold,
    logic="OR",
    n_iterations=1000,
    seed=42,
):
    """Compute bootstrap confidence intervals for given thresholds."""
    np.random.seed(seed)
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


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Optimize thresholds with proper train/val/test split or cross-validation"
    )
    parser.add_argument(
        "results_dir", type=Path, help="Path to validation results directory"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory (default: results_dir/threshold_analysis_cv)",
    )
    parser.add_argument(
        "--method",
        choices=["holdout", "cv"],
        default="holdout",
        help="Threshold selection method: 'holdout' (train/val/test split) or 'cv' (k-fold cross-validation)",
    )
    parser.add_argument(
        "--n-folds", type=int, default=5, help="Number of CV folds (for --method cv)"
    )
    parser.add_argument(
        "--train-frac",
        type=float,
        default=0.6,
        help="Training set fraction (for --method holdout)",
    )
    parser.add_argument(
        "--val-frac",
        type=float,
        default=0.2,
        help="Validation set fraction (for --method holdout)",
    )
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument(
        "--logic",
        choices=["OR", "AND", "MIN"],
        default="OR",
        help="Decision logic for combining thresholds",
    )

    args = parser.parse_args()

    if args.output_dir is None:
        args.output_dir = args.results_dir / "threshold_analysis_cv"

    args.output_dir.mkdir(exist_ok=True, parents=True)

    print("=" * 80)
    print("THRESHOLD OPTIMIZATION WITH PROPER TRAIN/VAL/TEST SPLIT")
    print("=" * 80)
    print(f"\nMethod: {args.method}")
    print(f"Logic: {args.logic}")
    print(f"Random seed: {args.seed}")
    print(f"Results directory: {args.results_dir}")
    print(f"Output directory: {args.output_dir}")
    print()

    # Load data
    predictions = load_predictions(args.results_dir)
    veracity_scores, alignment_scores, y_true = extract_scores_and_labels(predictions)

    print(f"Loaded {len(predictions)} samples")
    print(
        f"Ground truth: {sum(y_true)} misinformation, {len(y_true) - sum(y_true)} legitimate"
    )
    print()

    if args.method == "holdout":
        print(
            f"--- HOLDOUT METHOD (train={args.train_frac}, val={args.val_frac}, test={1-args.train_frac-args.val_frac}) ---"
        )
        print()

        # Split data
        train_data, val_data, test_data = stratified_split(
            veracity_scores,
            alignment_scores,
            y_true,
            train_frac=args.train_frac,
            val_frac=args.val_frac,
            seed=args.seed,
        )

        print(
            f"Train set: {len(train_data['indices'])} samples ({sum(train_data['y_true'])} misinformation)"
        )
        print(
            f"Val set:   {len(val_data['indices'])} samples ({sum(val_data['y_true'])} misinformation)"
        )
        print(
            f"Test set:  {len(test_data['indices'])} samples ({sum(test_data['y_true'])} misinformation)"
        )
        print()

        # Step 1: Optimize on train set
        print("Step 1: Grid search on TRAIN set...")
        _, best_on_train = sweep_thresholds(
            train_data["veracity_scores"],
            train_data["alignment_scores"],
            train_data["y_true"],
            logic=args.logic,
            metric="accuracy",
        )

        print(
            f"  Best thresholds on train: veracity={best_on_train['veracity_threshold']:.2f}, alignment={best_on_train['alignment_threshold']:.2f}"
        )
        print(f"  Train accuracy: {best_on_train['accuracy']:.1%}")
        print()

        # Step 2: Evaluate on validation set
        print("Step 2: Evaluate on VALIDATION set...")
        v_thresh = best_on_train["veracity_threshold"]
        a_thresh = best_on_train["alignment_threshold"]

        y_pred_val = apply_thresholds(
            val_data["veracity_scores"],
            val_data["alignment_scores"],
            v_thresh,
            a_thresh,
            args.logic,
        )

        val_metrics = {
            "accuracy": accuracy_score(val_data["y_true"], y_pred_val),
            "precision": precision_score(
                val_data["y_true"], y_pred_val, zero_division=0
            ),
            "recall": recall_score(val_data["y_true"], y_pred_val, zero_division=0),
            "f1": f1_score(val_data["y_true"], y_pred_val, zero_division=0),
        }

        print(f"  Val accuracy:  {val_metrics['accuracy']:.1%}")
        print(f"  Val precision: {val_metrics['precision']:.1%}")
        print(f"  Val recall:    {val_metrics['recall']:.1%}")
        print(f"  Val F1:        {val_metrics['f1']:.3f}")
        print()

        # Step 3: Final evaluation on held-out test set
        print("Step 3: Final evaluation on held-out TEST set...")
        y_pred_test = apply_thresholds(
            test_data["veracity_scores"],
            test_data["alignment_scores"],
            v_thresh,
            a_thresh,
            args.logic,
        )

        test_metrics = {
            "accuracy": accuracy_score(test_data["y_true"], y_pred_test),
            "precision": precision_score(
                test_data["y_true"], y_pred_test, zero_division=0
            ),
            "recall": recall_score(test_data["y_true"], y_pred_test, zero_division=0),
            "f1": f1_score(test_data["y_true"], y_pred_test, zero_division=0),
        }

        print(f"  Test accuracy:  {test_metrics['accuracy']:.1%}")
        print(f"  Test precision: {test_metrics['precision']:.1%}")
        print(f"  Test recall:    {test_metrics['recall']:.1%}")
        print(f"  Test F1:        {test_metrics['f1']:.3f}")
        print()

        # Step 4: Bootstrap CI on test set
        print("Step 4: Computing bootstrap 95% CI on TEST set (1000 iterations)...")
        test_ci = bootstrap_confidence_interval(
            test_data["veracity_scores"],
            test_data["alignment_scores"],
            test_data["y_true"],
            v_thresh,
            a_thresh,
            args.logic,
            n_iterations=1000,
            seed=args.seed,
        )

        print(
            f"  Accuracy:  {test_ci['accuracy']['mean']:.1%} [{test_ci['accuracy']['ci_lower']:.1%}, {test_ci['accuracy']['ci_upper']:.1%}]"
        )
        print(
            f"  Precision: {test_ci['precision']['mean']:.1%} [{test_ci['precision']['ci_lower']:.1%}, {test_ci['precision']['ci_upper']:.1%}]"
        )
        print(
            f"  Recall:    {test_ci['recall']['mean']:.1%} [{test_ci['recall']['ci_lower']:.1%}, {test_ci['recall']['ci_upper']:.1%}]"
        )
        print(
            f"  F1:        {test_ci['f1']['mean']:.3f} [{test_ci['f1']['ci_lower']:.3f}, {test_ci['f1']['ci_upper']:.3f}]"
        )
        print()

        # Save results
        output_file = (
            args.output_dir / f"holdout_optimization_{args.logic.lower()}.json"
        )
        with open(output_file, "w") as f:
            json.dump(
                {
                    "method": "holdout",
                    "logic": args.logic,
                    "random_seed": args.seed,
                    "split_config": {
                        "train_frac": args.train_frac,
                        "val_frac": args.val_frac,
                        "test_frac": 1 - args.train_frac - args.val_frac,
                    },
                    "split_sizes": {
                        "train": len(train_data["indices"]),
                        "val": len(val_data["indices"]),
                        "test": len(test_data["indices"]),
                    },
                    "optimal_thresholds": {
                        "veracity_threshold": v_thresh,
                        "alignment_threshold": a_thresh,
                    },
                    "train_metrics": {
                        "accuracy": best_on_train["accuracy"],
                        "precision": best_on_train["precision"],
                        "recall": best_on_train["recall"],
                        "f1": best_on_train["f1"],
                    },
                    "val_metrics": val_metrics,
                    "test_metrics": test_metrics,
                    "test_bootstrap_ci": test_ci,
                },
                f,
                indent=2,
            )

        print(f"✅ Saved: {output_file}")

    else:  # cv method
        print(f"--- CROSS-VALIDATION METHOD ({args.n_folds}-fold) ---")
        print()

        cv_results = cross_validate_thresholds(
            veracity_scores,
            alignment_scores,
            y_true,
            logic=args.logic,
            n_folds=args.n_folds,
            seed=args.seed,
        )

        print("Cross-validation complete:")
        print("  Recommended thresholds:")
        print(
            f"    Veracity:  {cv_results['recommended_thresholds']['veracity_threshold']:.2f}"
        )
        print(
            f"    Alignment: {cv_results['recommended_thresholds']['alignment_threshold']:.2f}"
        )
        print()
        print(f"  Mean validation metrics across {args.n_folds} folds:")
        print(
            f"    Accuracy:  {cv_results['mean_val_metrics']['accuracy']:.1%} ± {cv_results['std_val_metrics']['accuracy']:.1%}"
        )
        print(
            f"    Precision: {cv_results['mean_val_metrics']['precision']:.1%} ± {cv_results['std_val_metrics']['precision']:.1%}"
        )
        print(
            f"    Recall:    {cv_results['mean_val_metrics']['recall']:.1%} ± {cv_results['std_val_metrics']['recall']:.1%}"
        )
        print(
            f"    F1:        {cv_results['mean_val_metrics']['f1']:.3f} ± {cv_results['std_val_metrics']['f1']:.3f}"
        )
        print()

        # Evaluate recommended thresholds on full dataset for comparison
        print(
            "Evaluating recommended thresholds on FULL dataset (for comparison only)..."
        )
        v_thresh = cv_results["recommended_thresholds"]["veracity_threshold"]
        a_thresh = cv_results["recommended_thresholds"]["alignment_threshold"]

        y_pred_full = apply_thresholds(
            veracity_scores, alignment_scores, v_thresh, a_thresh, args.logic
        )

        full_metrics = {
            "accuracy": accuracy_score(y_true, y_pred_full),
            "precision": precision_score(y_true, y_pred_full, zero_division=0),
            "recall": recall_score(y_true, y_pred_full, zero_division=0),
            "f1": f1_score(y_true, y_pred_full, zero_division=0),
        }

        print("  Full dataset metrics:")
        print(f"    Accuracy:  {full_metrics['accuracy']:.1%}")
        print(f"    Precision: {full_metrics['precision']:.1%}")
        print(f"    Recall:    {full_metrics['recall']:.1%}")
        print(f"    F1:        {full_metrics['f1']:.3f}")
        print()

        # Bootstrap CI on full dataset
        print("Computing bootstrap 95% CI on FULL dataset (1000 iterations)...")
        full_ci = bootstrap_confidence_interval(
            veracity_scores,
            alignment_scores,
            y_true,
            v_thresh,
            a_thresh,
            args.logic,
            n_iterations=1000,
            seed=args.seed,
        )

        print(
            f"  Accuracy:  {full_ci['accuracy']['mean']:.1%} [{full_ci['accuracy']['ci_lower']:.1%}, {full_ci['accuracy']['ci_upper']:.1%}]"
        )
        print(
            f"  Precision: {full_ci['precision']['mean']:.1%} [{full_ci['precision']['ci_lower']:.1%}, {full_ci['precision']['ci_upper']:.1%}]"
        )
        print(
            f"  Recall:    {full_ci['recall']['mean']:.1%} [{full_ci['recall']['ci_lower']:.1%}, {full_ci['recall']['ci_upper']:.1%}]"
        )
        print(
            f"  F1:        {full_ci['f1']['mean']:.3f} [{full_ci['f1']['ci_lower']:.3f}, {full_ci['f1']['ci_upper']:.3f}]"
        )
        print()

        # Save results
        output_file = args.output_dir / f"cv_optimization_{args.logic.lower()}.json"
        with open(output_file, "w") as f:
            json.dump(
                {
                    "method": "cross_validation",
                    "logic": args.logic,
                    "random_seed": args.seed,
                    "n_folds": args.n_folds,
                    "cv_results": cv_results,
                    "full_dataset_metrics": full_metrics,
                    "full_dataset_bootstrap_ci": full_ci,
                },
                f,
                indent=2,
            )

        print(f"✅ Saved: {output_file}")

    print()
    print("=" * 80)
    print("COMPLETE")
    print("=" * 80)
    print()
    print("IMPORTANT NOTES:")
    print("  1. Thresholds were optimized on a separate dataset (train or CV folds)")
    print(
        "  2. Final metrics are reported on held-out data that was NOT used for threshold selection"
    )
    print(
        "  3. This methodology avoids test-set contamination and provides unbiased performance estimates"
    )
    print()


if __name__ == "__main__":
    main()
