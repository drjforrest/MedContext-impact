#!/usr/bin/env python3
"""Generate Recharts-compatible data from validation results."""

import json
import sys
from pathlib import Path


def load_validation_results(results_dir: Path):
    """Load validation results."""
    raw_predictions = results_dir / "raw_predictions.json"
    validation_report = results_dir / "validation_report.json"

    with open(raw_predictions) as f:
        predictions = json.load(f)

    with open(validation_report) as f:
        report = json.load(f)

    return predictions, report


def generate_confusion_matrix(predictions):
    """Generate confusion matrix data for misinformation detection.

    Classification Logic:
    - Positive class: Misinformation (is_misinformation=True)
    - Negative class: Legitimate (is_misinformation=False)
    - TP: Correctly flagged misinformation
    - FP: Legitimate content incorrectly flagged as misinformation
    - TN: Legitimate content correctly identified as legitimate
    - FN: Misinformation incorrectly marked as legitimate (missed)
    """
    tp = fp = tn = fn = 0

    for pred in predictions:
        gt_misinfo = pred["ground_truth"].get("is_misinformation", False)
        pred_misinfo = pred["predictions"]["combined_analysis"].get(
            "is_misinformation", False
        )

        if gt_misinfo and pred_misinfo:
            tp += 1
        elif not gt_misinfo and pred_misinfo:
            fp += 1
        elif not gt_misinfo and not pred_misinfo:
            tn += 1
        else:
            fn += 1

    return {
        "confusion_matrix": [
            {
                "name": "True Positive (Correctly Flagged Misinformation)",
                "short_name": "True Positive",
                "value": tp,
                "description": "Misinformation correctly identified as misinformation",
            },
            {
                "name": "False Positive (Legitimate Flagged as Misinformation)",
                "short_name": "False Positive",
                "value": fp,
                "description": "Legitimate content incorrectly flagged as misinformation",
            },
            {
                "name": "True Negative (Correctly Identified Legitimate)",
                "short_name": "True Negative",
                "value": tn,
                "description": "Legitimate content correctly identified as legitimate",
            },
            {
                "name": "False Negative (Missed Misinformation)",
                "short_name": "False Negative",
                "value": fn,
                "description": "Misinformation incorrectly marked as legitimate (missed detection)",
            },
        ],
        "matrix_grid": [
            {
                "actual": "Misinformation (Positive)",
                "predicted": "Misinformation (Positive)",
                "count": tp,
                "label": "TP",
            },
            {
                "actual": "Misinformation (Positive)",
                "predicted": "Legitimate (Negative)",
                "count": fn,
                "label": "FN",
            },
            {
                "actual": "Legitimate (Negative)",
                "predicted": "Misinformation (Positive)",
                "count": fp,
                "label": "FP",
            },
            {
                "actual": "Legitimate (Negative)",
                "predicted": "Legitimate (Negative)",
                "count": tn,
                "label": "TN",
            },
        ],
    }


def generate_score_distributions(predictions):
    """Generate score distribution data with semantic category labels.

    Veracity Categories:
    - true (0.9): Claim is factually and medically well-supported
    - partially_true (0.6): Claim has some basis but contains inaccuracies
    - false (0.1): Claim is factually unsupported or medically incorrect

    Alignment Categories:
    - aligns_fully (0.9): Image directly supports/illustrates the claim
    - partially_aligns (0.6): Image relates to claim but doesn't fully support it
    - does_not_align (0.1): Image is unrelated or contradicts the claim

    Classification Threshold: score > 0.5 = positive (plausible/aligned)
    """
    veracity_scores = []
    alignment_scores = []

    # Category label mappings for better readability
    veracity_labels = {
        "true": "True (0.9) - Well-supported claim",
        "partially_true": "Partially True (0.6) - Mixed accuracy",
        "false": "False (0.1) - Unsupported claim",
    }

    alignment_labels = {
        "aligns_fully": "Fully Aligned (0.9) - Image supports claim",
        "partially_aligns": "Partially Aligned (0.6) - Image relates but doesn't support",
        "does_not_align": "Does Not Align (0.1) - Image unrelated/contradicts",
    }

    for pred in predictions:
        context = pred["predictions"]["contextual_analysis"]
        gt = pred["ground_truth"]

        veracity_cat = context.get("veracity_category", "unknown")
        alignment_cat = context.get("alignment_category", "unknown")

        veracity_scores.append(
            {
                "score": context.get("veracity_score", 0.5),
                "category": veracity_cat,
                "category_label": veracity_labels.get(veracity_cat, veracity_cat),
                "ground_truth": gt.get("plausibility", "unknown"),
                "is_misinformation": gt.get("is_misinformation", False),
                "predicted_positive": context.get("veracity_score", 0.5) > 0.5,
            }
        )

        alignment_scores.append(
            {
                "score": context.get("alignment_score", 0.5),
                "category": alignment_cat,
                "category_label": alignment_labels.get(alignment_cat, alignment_cat),
                "ground_truth": gt.get("alignment", "unknown"),
                "is_misinformation": gt.get("is_misinformation", False),
                "predicted_positive": context.get("alignment_score", 0.5) > 0.5,
            }
        )

    return {
        "veracity_distribution": veracity_scores,
        "alignment_distribution": alignment_scores,
        "score_metadata": {
            "veracity_mapping": veracity_labels,
            "alignment_mapping": alignment_labels,
            "threshold": 0.5,
            "threshold_note": "score > 0.5 classified as positive (plausible/aligned)",
        },
    }


def generate_performance_comparison(predictions):
    """Compare performance of different detection methods."""
    methods = {
        "Pixel Forensics": {"correct": 0, "total": 0},
        "Veracity Only": {"correct": 0, "total": 0},
        "Alignment Only": {"correct": 0, "total": 0},
        "Combined System": {"correct": 0, "total": 0},
    }

    for pred in predictions:
        gt_misinfo = pred["ground_truth"].get("is_misinformation", False)

        # Pixel forensics
        pixel_pred = not pred["predictions"]["pixel_forensics"].get(
            "pixel_authentic", True
        )
        if pixel_pred == gt_misinfo:
            methods["Pixel Forensics"]["correct"] += 1
        methods["Pixel Forensics"]["total"] += 1

        # Veracity only
        context = pred["predictions"]["contextual_analysis"]
        veracity_pred = (
            context.get("veracity_category") == "false"
            or context.get("veracity_score", 0.5) < 0.5
        )
        if veracity_pred == gt_misinfo:
            methods["Veracity Only"]["correct"] += 1
        methods["Veracity Only"]["total"] += 1

        # Alignment only
        alignment_pred = (
            context.get("alignment_category") == "does_not_align"
            or context.get("alignment_score", 0.5) < 0.5
        )
        if alignment_pred == gt_misinfo:
            methods["Alignment Only"]["correct"] += 1
        methods["Alignment Only"]["total"] += 1

        # Combined
        combined_pred = pred["predictions"]["combined_analysis"].get(
            "is_misinformation", False
        )
        if combined_pred == gt_misinfo:
            methods["Combined System"]["correct"] += 1
        methods["Combined System"]["total"] += 1

    return {
        "method_comparison": [
            {
                "method": name,
                "accuracy": (
                    (stats["correct"] / stats["total"] * 100)
                    if stats["total"] > 0
                    else 0
                ),
                "correct": stats["correct"],
                "total": stats["total"],
            }
            for name, stats in methods.items()
        ]
    }


def generate_sample_details(predictions):
    """Generate per-sample detail data."""
    samples = []

    for i, pred in enumerate(predictions):
        gt = pred["ground_truth"]
        context = pred["predictions"]["contextual_analysis"]
        combined = pred["predictions"]["combined_analysis"]
        pixel = pred["predictions"]["pixel_forensics"]

        samples.append(
            {
                "id": pred.get("image_id", f"sample_{i}"),
                "ground_truth": {
                    "is_misinformation": gt.get("is_misinformation", False),
                    "plausibility": gt.get("plausibility", "unknown"),
                    "alignment": gt.get("alignment", "unknown"),
                    "pixel_authentic": gt.get("pixel_authentic", True),
                },
                "predictions": {
                    "is_misinformation": combined.get("is_misinformation", False),
                    "veracity_score": context.get("veracity_score", 0.5),
                    "veracity_category": context.get("veracity_category", "unknown"),
                    "alignment_score": context.get("alignment_score", 0.5),
                    "alignment_category": context.get("alignment_category", "unknown"),
                    "pixel_authentic": pixel.get("pixel_authentic", True),
                },
                "correct": gt.get("is_misinformation", False)
                == combined.get("is_misinformation", False),
            }
        )

    return {"samples": samples}


def generate_metric_summary(predictions):
    """Generate summary metrics."""
    # Calculate all metrics
    tp = sum(
        1
        for p in predictions
        if p["ground_truth"].get("is_misinformation")
        and p["predictions"]["combined_analysis"].get("is_misinformation")
    )
    fp = sum(
        1
        for p in predictions
        if not p["ground_truth"].get("is_misinformation")
        and p["predictions"]["combined_analysis"].get("is_misinformation")
    )
    tn = sum(
        1
        for p in predictions
        if not p["ground_truth"].get("is_misinformation")
        and not p["predictions"]["combined_analysis"].get("is_misinformation")
    )
    fn = sum(
        1
        for p in predictions
        if p["ground_truth"].get("is_misinformation")
        and not p["predictions"]["combined_analysis"].get("is_misinformation")
    )

    accuracy = (tp + tn) / len(predictions) if predictions else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = (
        2 * (precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0
    )

    return {
        "summary_metrics": [
            {"metric": "Accuracy", "value": accuracy * 100},
            {"metric": "Precision", "value": precision * 100},
            {"metric": "Recall", "value": recall * 100},
            {"metric": "F1 Score", "value": f1 * 100},
        ],
        "raw_metrics": {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn,
        },
    }


def generate_charts(results_dir: Path) -> None:
    """Generate chart_data.json from a completed validation results directory.

    Can be called programmatically (e.g. from validate_med_mmhl.py) or via CLI.
    """
    results_dir = Path(results_dir)
    if not results_dir.exists():
        raise FileNotFoundError(f"Results directory not found: {results_dir}")

    print(f"Loading validation results from {results_dir}...")
    predictions, report = load_validation_results(results_dir)

    print(f"Generating chart data for {len(predictions)} samples...")

    model_name = results_dir.name
    model_label = "Unknown Model"
    if "vertex" in model_name.lower() and "27b" in model_name.lower():
        model_label = "MedGemma 27B Multimodal (Vertex AI)"
    elif "27b" in model_name.lower():
        model_label = "MedGemma 27B (HuggingFace Inference API)"
    elif "4b" in model_name.lower():
        model_label = "MedGemma 4B (Quantized Local)"
    elif "quantized" in model_name.lower():
        model_label = "MedGemma Quantized Model"
    elif "hf" in model_name.lower():
        model_label = "MedGemma HuggingFace Model"

    chart_data = {
        "metadata": {
            "total_samples": len(predictions),
            "dataset": report.get("dataset", "Unknown"),
            "timestamp": report.get("timestamp", ""),
            "model_name": model_name,
            "model_label": model_label,
            "sampling_method": report.get("sampling_method", "unknown"),
            "random_seed": report.get("random_seed", None),
            "classification_info": {
                "positive_class": "Misinformation (is_misinformation=True)",
                "negative_class": "Legitimate (is_misinformation=False)",
                "veracity_threshold": 0.5,
                "alignment_threshold": 0.5,
                "threshold_note": "Veracity score > 0.5 = plausible (not fake). Alignment score > 0.5 = aligned.",
                "optimization_available": "See threshold_analysis/ subdirectory for optimized thresholds",
            },
        }
    }

    chart_data.update(generate_confusion_matrix(predictions))
    chart_data.update(generate_score_distributions(predictions))
    chart_data.update(generate_performance_comparison(predictions))
    chart_data.update(generate_sample_details(predictions))
    chart_data.update(generate_metric_summary(predictions))

    output_file = results_dir / "chart_data.json"
    with open(output_file, "w") as f:
        json.dump(chart_data, f, indent=2)

    print(f"\n✅ Chart data generated: {output_file}")
    print(f"\nModel: {model_label}")
    print("Summary:")
    print(f"  - Accuracy: {chart_data['raw_metrics']['accuracy'] * 100:.1f}%")
    print(f"  - Precision: {chart_data['raw_metrics']['precision'] * 100:.1f}%")
    print(f"  - Recall: {chart_data['raw_metrics']['recall'] * 100:.1f}%")
    print(f"  - F1 Score: {chart_data['raw_metrics']['f1'] * 100:.1f}%")
    print("\nClassification Info:")
    print("  - Positive class: Misinformation")
    print("  - Threshold: 0.5 (combined decision logic)")
    print(
        "  - Optimization: See threshold_analysis/ for model-specific optimal thresholds"
    )


def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_validation_charts.py <results_dir>")
        sys.exit(1)

    results_dir = Path(sys.argv[1])
    try:
        generate_charts(results_dir)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
