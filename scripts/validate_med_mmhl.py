#!/usr/bin/env python3
"""Validate MedContext on Med-MMHL multimodal claim dataset.

This is the proper validation study (not Proof of Justification).
Uses Med-MMHL image-claim pairs with fact-checker labels.

Usage:
  # 1. Download Med-MMHL (see scripts/download_med_mmhl.py)
  # 2. Run validation on test split with randomized sampling:

  python scripts/validate_med_mmhl.py \
    --data-dir data/med-mmhl \
    --split test \
    --limit 163 \
    --random-seed 42 \
    --output validation_results/med_mmhl_n163_randomized

  # Sequential sampling (original - has 14pp bias toward misinformation):

  python scripts/validate_med_mmhl.py \
    --data-dir data/med-mmhl \
    --split test \
    --limit 163 \
    --output validation_results/med_mmhl_n163_sequential

  # Full test set (no limit):

  python scripts/validate_med_mmhl.py \
    --data-dir data/med-mmhl \
    --split test \
    --output validation_results/med_mmhl_full_test

  # With medical-only filter (after annotating):

  python scripts/validate_med_mmhl.py \
    --data-dir data/med-mmhl \
    --annotations data/med-mmhl/image_type_annotations.json \
    --require-medical \
    --output validation_results/med_mmhl_medical_v1

  # Bootstrap confidence intervals (slower):

  python scripts/validate_med_mmhl.py \
    --data-dir data/med-mmhl \
    --bootstrap 1000 \
    --output validation_results/med_mmhl_v1
"""

import argparse
import importlib.util
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

# Add repo root and scripts to path
repo_root = Path(__file__).parent.parent
scripts_dir = Path(__file__).parent
sys.path.insert(0, str(repo_root / "src"))
sys.path.insert(0, str(scripts_dir))

from app.validation.loaders import load_med_mmhl_dataset  # noqa: E402
from app.validation.metrics import (  # noqa: E402
    bootstrap_confidence_intervals,
    compute_three_dimensional_metrics,
)

target_path = scripts_dir / "validate_three_methods.py"
_spec = importlib.util.spec_from_file_location(
    "validate_three_methods",
    target_path,
)
if _spec is None:
    raise FileNotFoundError(
        f"Could not load module spec from {target_path}. "
        "Ensure validate_three_methods.py exists in the scripts directory."
    )
if _spec.loader is None:
    raise RuntimeError(
        f"Module spec for {target_path} has no loader. "
        "The file may be corrupted or inaccessible."
    )
vtm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vtm)
ThreeMethodValidator = vtm.ThreeMethodValidator


def run_validation(
    data_dir: Path,
    split: str = "test",
    annotations_path: Path | None = None,
    require_medical: bool = False,
    output_dir: Path = Path("validation_results/med_mmhl"),
    bootstrap_iterations: int = 0,
    limit: int | None = None,
    random_seed: int | None = None,
) -> dict:
    """Run MedContext validation on Med-MMHL."""
    # Support both: benchmarked_data/image_article/ and image_article/ directly
    benchmark_path = data_dir / "benchmarked_data"
    if not benchmark_path.exists() and (data_dir / "image_article").exists():
        benchmark_path = data_dir
    base_image_dir = data_dir

    # Detect model from output directory name
    model_name = output_dir.name
    model_label = "Unknown Model"
    if "27b" in model_name.lower():
        model_label = "MedGemma 27B (HuggingFace Inference API)"
    elif "4b" in model_name.lower() and "quantized" in model_name.lower():
        model_label = "MedGemma 4B (Quantized Local)"
    elif "4b" in model_name.lower():
        model_label = "MedGemma 4B"
    elif "quantized" in model_name.lower():
        model_label = "MedGemma Quantized Model"
    elif "hf" in model_name.lower():
        model_label = "MedGemma HuggingFace Model"

    records = load_med_mmhl_dataset(
        benchmark_path=benchmark_path,
        split=split,
        base_image_dir=base_image_dir,
        annotations_path=annotations_path,
        require_medical=require_medical,
    )

    if not records:
        raise ValueError("No records loaded. Check data_dir and annotations.")

    # Apply limit with optional randomization
    if limit:
        if random_seed is not None:
            # Randomized sampling with seed for reproducibility
            random.seed(random_seed)
            records = random.sample(records, min(limit, len(records)))
            sampling_method = f"simple_random_seed_{random_seed}"
        else:
            # Sequential sampling (original behavior)
            records = records[:limit]
            sampling_method = "sequential_first_n"
    else:
        sampling_method = "full_dataset"

    # Convert to format expected by ThreeMethodValidator
    # ThreeMethodValidator expects: image_path, claim, ground_truth
    dataset = []
    for r in records:
        gt = r["ground_truth"]
        dataset.append(
            {
                "image_id": r["image_id"],
                "image_path": r["image_path"],
                "claim": r["claim"],
                "ground_truth": {
                    "pixel_authentic": gt.get("pixel_authentic", True),
                    "alignment": (
                        "misaligned" if gt.get("expected_misalignment") else "aligned"
                    ),
                    "plausibility": "low" if gt.get("is_fake_claim") else "high",
                    "is_misinformation": gt.get("is_fake_claim", False),
                },
            }
        )

    # Write temporary dataset for validator
    temp_dataset = output_dir / "med_mmhl_dataset.json"
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(temp_dataset, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    # Run validation using ThreeMethodValidator
    validator = ThreeMethodValidator(
        dataset_path=temp_dataset,
        output_dir=output_dir,
    )
    validator.run_validation()

    # Map validator results to metrics format
    predictions = []
    ground_truth = []
    for result in validator.results:
        pred = result["predictions"]["contextual_analysis"]
        pixel = result["predictions"]["pixel_forensics"]
        gt = result["ground_truth"]

        predictions.append(
            {
                "pixel_authentic": pixel.get("pixel_authentic", True),
                "veracity_score": pred.get("veracity_score", 0.5),
                "alignment_score": pred.get("alignment_score", 0.5),
            }
        )
        ground_truth.append(
            {
                "is_fake_claim": gt.get("is_misinformation", False),
                "expected_misalignment": gt.get("alignment") == "misaligned",
            }
        )

    # Compute metrics
    metrics = compute_three_dimensional_metrics(predictions, ground_truth)

    # Bootstrap CI if requested
    if bootstrap_iterations > 0 and len(predictions) >= 10:
        ci = bootstrap_confidence_intervals(
            predictions,
            ground_truth,
            n_iterations=bootstrap_iterations,
        )
        metrics["bootstrap_95ci"] = ci

    # Save results
    report = {
        "dataset": "Med-MMHL",
        "split": split,
        "model_name": model_name,
        "model_label": model_label,
        "n_samples": len(validator.results),
        "n_skipped_missing": validator.skipped_missing,
        "n_skipped_errors": validator.skipped_errors,
        "require_medical": require_medical,
        "sampling_method": sampling_method,
        "random_seed": random_seed if random_seed is not None else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classification_info": {
            "veracity": {
                "threshold": 0.5,
                "positive_class": "Plausible (not fake)",
                "negative_class": "Fake claim",
                "decision_rule": "veracity_score > 0.5 = plausible",
                "score_mapping": {"true": 0.9, "partially_true": 0.6, "false": 0.1},
                "note": "High recall/low precision suggests threshold=0.65 may be optimal (excludes partially_true)",
            },
            "alignment": {
                "threshold": 0.5,
                "positive_class": "Aligned",
                "negative_class": "Misaligned",
                "decision_rule": "alignment_score > 0.5 = aligned",
                "score_mapping": {
                    "aligns_fully": 0.9,
                    "partially_aligns": 0.6,
                    "does_not_align": 0.1,
                },
            },
            "misinformation": {
                "positive_class": "Misinformation",
                "negative_class": "Legitimate",
                "decision_logic": "Combined veracity-first logic (see ThreeMethodValidator._compute_final_verdict)",
            },
        },
        "metrics": metrics,
    }

    report_path = output_dir / "validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Save raw predictions for analysis
    raw_path = output_dir / "raw_predictions.json"
    with open(raw_path, "w", encoding="utf-8") as f:
        json.dump(validator.results, f, indent=2, default=str)

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate MedContext on Med-MMHL")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/med-mmhl"),
        help="Med-MMHL data directory",
    )
    parser.add_argument(
        "--split",
        choices=["train", "dev", "test"],
        default="test",
        help="Dataset split (default: test)",
    )
    parser.add_argument(
        "--annotations",
        type=Path,
        default=None,
        help="Path to image_type_annotations.json for medical filtering",
    )
    parser.add_argument(
        "--require-medical",
        action="store_true",
        help="Filter to medical images only (requires annotations)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("validation_results/med_mmhl_v1"),
        help="Output directory",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=0,
        help="Bootstrap iterations for 95%% CI (0=disable)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit samples for quick test",
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=None,
        help="Random seed for reproducible sampling (requires --limit)",
    )
    args = parser.parse_args()

    if args.random_seed is not None and args.limit is None:
        print("Error: --random-seed requires --limit to be set")
        return 1

    if args.require_medical and not args.annotations:
        print("Error: --require-medical requires --annotations")
        return 1

    if (
        not (args.data_dir / "benchmarked_data").exists()
        and not (args.data_dir / "image_article").exists()
    ):
        print(f"Error: Data not found at {args.data_dir}")
        print("Run scripts/download_med_mmhl.py first to verify setup.")
        return 1

    try:
        report = run_validation(
            data_dir=args.data_dir,
            split=args.split,
            annotations_path=args.annotations,
            require_medical=args.require_medical,
            output_dir=args.output,
            bootstrap_iterations=args.bootstrap,
            limit=args.limit,
            random_seed=args.random_seed,
        )
    except Exception as e:
        print(f"Error: {e}")
        return 1

    # Auto-generate chart data for UI
    try:
        import importlib.util as _ilu

        _charts_path = Path(__file__).parent / "generate_validation_charts.py"
        _spec = _ilu.spec_from_file_location("generate_validation_charts", _charts_path)
        if _spec and _spec.loader:
            _charts_mod = _ilu.module_from_spec(_spec)
            _spec.loader.exec_module(_charts_mod)
            _charts_mod.generate_charts(args.output)
            print(f"\nChart data: {args.output / 'chart_data.json'}")
    except Exception as chart_err:
        print(f"\nWarning: Chart generation failed: {chart_err}")

    # Print summary
    m = report["metrics"]
    print()
    print("=" * 60)
    print("Med-MMHL Validation Results")
    print("=" * 60)
    print(f"Model: {report.get('model_label', 'Unknown')}")
    print(f"Split: {report['split']} | n={report['n_samples']}")
    if "sampling_method" in report:
        print(f"Sampling: {report['sampling_method']}")
        if report.get("random_seed"):
            print(f"Random seed: {report['random_seed']}")
    print()
    print("Classification Info:")
    print(
        f"  Veracity threshold: {report['classification_info']['veracity']['threshold']}"
    )
    print(
        f"  Positive class: {report['classification_info']['veracity']['positive_class']}"
    )
    print("  Score mapping: true=0.9, partially_true=0.6, false=0.1")
    print()
    print("Pixel Authenticity (rate marked authentic):")
    print(f"  {m['pixel_authenticity']['mean_authentic_rate']:.1%}")
    print()
    print("Veracity (claim plausibility):")
    v_f1 = m["veracity"]["f1"]
    v_f1_str = f"{v_f1:.3f}" if v_f1 is not None else "N/A"
    print(f"  Accuracy: {m['veracity']['accuracy']:.1%} | F1: {v_f1_str}")
    if m["veracity"].get("precision") and m["veracity"].get("recall"):
        print(
            f"  Precision: {m['veracity']['precision']:.1%} | Recall: {m['veracity']['recall']:.1%}"
        )
    print()
    print("Alignment (image-claim consistency):")
    a_f1 = m["alignment"]["f1"]
    a_f1_str = f"{a_f1:.3f}" if a_f1 is not None else "N/A"
    print(f"  Accuracy: {m['alignment']['accuracy']:.1%} | F1: {a_f1_str}")
    if m["alignment"].get("precision") and m["alignment"].get("recall"):
        print(
            f"  Precision: {m['alignment']['precision']:.1%} | Recall: {m['alignment']['recall']:.1%}"
        )
    if "bootstrap_95ci" in m:
        ci = m["bootstrap_95ci"]
        print()
        print("Bootstrap 95% CI:")
        print(
            f"  Veracity accuracy:   {ci['veracity_accuracy']['mean']:.1%} [{ci['veracity_accuracy']['ci_lower']:.1%}, {ci['veracity_accuracy']['ci_upper']:.1%}]"
        )
        print(
            f"  Alignment accuracy: {ci['alignment_accuracy']['mean']:.1%} [{ci['alignment_accuracy']['ci_lower']:.1%}, {ci['alignment_accuracy']['ci_upper']:.1%}]"
        )
    print()
    print(f"Report: {args.output / 'validation_report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
