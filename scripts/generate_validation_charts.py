#!/usr/bin/env python3
"""Generate Recharts-compatible data from validation results."""
import json
import sys
from pathlib import Path
from collections import defaultdict

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
    """Generate confusion matrix data for misinformation detection."""
    tp = fp = tn = fn = 0

    for pred in predictions:
        gt_misinfo = pred['ground_truth'].get('is_misinformation', False)
        pred_misinfo = pred['predictions']['combined_analysis'].get('is_misinformation', False)

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
            {"name": "True Positive", "value": tp},
            {"name": "False Positive", "value": fp},
            {"name": "True Negative", "value": tn},
            {"name": "False Negative", "value": fn}
        ],
        "matrix_grid": [
            {"actual": "Misinformation", "predicted": "Misinformation", "count": tp},
            {"actual": "Misinformation", "predicted": "Legitimate", "count": fn},
            {"actual": "Legitimate", "predicted": "Misinformation", "count": fp},
            {"actual": "Legitimate", "predicted": "Legitimate", "count": tn}
        ]
    }

def generate_score_distributions(predictions):
    """Generate score distribution data."""
    veracity_scores = []
    alignment_scores = []

    for pred in predictions:
        context = pred['predictions']['contextual_analysis']
        gt = pred['ground_truth']

        veracity_scores.append({
            "score": context.get('veracity_score', 0.5),
            "category": context.get('veracity_category', 'unknown'),
            "ground_truth": gt.get('plausibility', 'unknown'),
            "is_misinformation": gt.get('is_misinformation', False)
        })

        alignment_scores.append({
            "score": context.get('alignment_score', 0.5),
            "category": context.get('alignment_category', 'unknown'),
            "ground_truth": gt.get('alignment', 'unknown'),
            "is_misinformation": gt.get('is_misinformation', False)
        })

    return {
        "veracity_distribution": veracity_scores,
        "alignment_distribution": alignment_scores
    }

def generate_performance_comparison(predictions):
    """Compare performance of different detection methods."""
    methods = {
        "Pixel Forensics": {"correct": 0, "total": 0},
        "Veracity Only": {"correct": 0, "total": 0},
        "Alignment Only": {"correct": 0, "total": 0},
        "Combined System": {"correct": 0, "total": 0}
    }

    for pred in predictions:
        gt_misinfo = pred['ground_truth'].get('is_misinformation', False)

        # Pixel forensics
        pixel_pred = not pred['predictions']['pixel_forensics'].get('pixel_authentic', True)
        if pixel_pred == gt_misinfo:
            methods["Pixel Forensics"]["correct"] += 1
        methods["Pixel Forensics"]["total"] += 1

        # Veracity only
        context = pred['predictions']['contextual_analysis']
        veracity_pred = context.get('veracity_category') == 'false' or context.get('veracity_score', 0.5) < 0.5
        if veracity_pred == gt_misinfo:
            methods["Veracity Only"]["correct"] += 1
        methods["Veracity Only"]["total"] += 1

        # Alignment only
        alignment_pred = context.get('alignment_category') == 'does_not_align' or context.get('alignment_score', 0.5) < 0.5
        if alignment_pred == gt_misinfo:
            methods["Alignment Only"]["correct"] += 1
        methods["Alignment Only"]["total"] += 1

        # Combined
        combined_pred = pred['predictions']['combined_analysis'].get('is_misinformation', False)
        if combined_pred == gt_misinfo:
            methods["Combined System"]["correct"] += 1
        methods["Combined System"]["total"] += 1

    return {
        "method_comparison": [
            {
                "method": name,
                "accuracy": (stats["correct"] / stats["total"] * 100) if stats["total"] > 0 else 0,
                "correct": stats["correct"],
                "total": stats["total"]
            }
            for name, stats in methods.items()
        ]
    }

def generate_sample_details(predictions):
    """Generate per-sample detail data."""
    samples = []

    for i, pred in enumerate(predictions):
        gt = pred['ground_truth']
        context = pred['predictions']['contextual_analysis']
        combined = pred['predictions']['combined_analysis']
        pixel = pred['predictions']['pixel_forensics']

        samples.append({
            "id": pred.get('image_id', f"sample_{i}"),
            "ground_truth": {
                "is_misinformation": gt.get('is_misinformation', False),
                "plausibility": gt.get('plausibility', 'unknown'),
                "alignment": gt.get('alignment', 'unknown'),
                "pixel_authentic": gt.get('pixel_authentic', True)
            },
            "predictions": {
                "is_misinformation": combined.get('is_misinformation', False),
                "veracity_score": context.get('veracity_score', 0.5),
                "veracity_category": context.get('veracity_category', 'unknown'),
                "alignment_score": context.get('alignment_score', 0.5),
                "alignment_category": context.get('alignment_category', 'unknown'),
                "pixel_authentic": pixel.get('pixel_authentic', True)
            },
            "correct": gt.get('is_misinformation', False) == combined.get('is_misinformation', False)
        })

    return {"samples": samples}

def generate_metric_summary(predictions):
    """Generate summary metrics."""
    # Calculate all metrics
    tp = sum(1 for p in predictions if p['ground_truth'].get('is_misinformation') and p['predictions']['combined_analysis'].get('is_misinformation'))
    fp = sum(1 for p in predictions if not p['ground_truth'].get('is_misinformation') and p['predictions']['combined_analysis'].get('is_misinformation'))
    tn = sum(1 for p in predictions if not p['ground_truth'].get('is_misinformation') and not p['predictions']['combined_analysis'].get('is_misinformation'))
    fn = sum(1 for p in predictions if p['ground_truth'].get('is_misinformation') and not p['predictions']['combined_analysis'].get('is_misinformation'))

    accuracy = (tp + tn) / len(predictions) if predictions else 0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0

    return {
        "summary_metrics": [
            {"metric": "Accuracy", "value": accuracy * 100},
            {"metric": "Precision", "value": precision * 100},
            {"metric": "Recall", "value": recall * 100},
            {"metric": "F1 Score", "value": f1 * 100}
        ],
        "raw_metrics": {
            "accuracy": accuracy,
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "tp": tp,
            "fp": fp,
            "tn": tn,
            "fn": fn
        }
    }

def main():
    if len(sys.argv) < 2:
        print("Usage: python generate_validation_charts.py <results_dir>")
        sys.exit(1)

    results_dir = Path(sys.argv[1])

    if not results_dir.exists():
        print(f"Error: Directory not found: {results_dir}")
        sys.exit(1)

    print(f"Loading validation results from {results_dir}...")
    predictions, report = load_validation_results(results_dir)

    print(f"Generating chart data for {len(predictions)} samples...")

    # Generate all chart data
    chart_data = {
        "metadata": {
            "total_samples": len(predictions),
            "dataset": report.get("dataset", "Unknown"),
            "timestamp": report.get("timestamp", ""),
        }
    }

    chart_data.update(generate_confusion_matrix(predictions))
    chart_data.update(generate_score_distributions(predictions))
    chart_data.update(generate_performance_comparison(predictions))
    chart_data.update(generate_sample_details(predictions))
    chart_data.update(generate_metric_summary(predictions))

    # Save chart data
    output_file = results_dir / "chart_data.json"
    with open(output_file, 'w') as f:
        json.dump(chart_data, f, indent=2)

    print(f"\n✅ Chart data generated: {output_file}")
    print(f"\nSummary:")
    print(f"  - Accuracy: {chart_data['raw_metrics']['accuracy']*100:.1f}%")
    print(f"  - Precision: {chart_data['raw_metrics']['precision']*100:.1f}%")
    print(f"  - Recall: {chart_data['raw_metrics']['recall']*100:.1f}%")
    print(f"  - F1 Score: {chart_data['raw_metrics']['f1']:.3f}")

if __name__ == "__main__":
    main()
