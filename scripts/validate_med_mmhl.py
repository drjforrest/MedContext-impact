#!/usr/bin/env python3
"""Validate MedContext on Med-MMHL multimodal claim dataset.

This is the proper validation study (not Proof of Justification).
Uses Med-MMHL image-claim pairs with fact-checker labels.

Usage:
  # 1. Download Med-MMHL (see scripts/download_med_mmhl.py)
  # 2. Run validation on test split:

  python scripts/validate_med_mmhl.py \
    --data-dir data/med-mmhl \
    --split test \
    --output validation_results/med_mmhl_v1

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

from app.validation.loaders import load_med_mmhl_dataset
from app.validation.metrics import (
    compute_three_dimensional_metrics,
    bootstrap_confidence_intervals,
)

import importlib.util

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
            sampling_method = f"stratified_random_seed_{random_seed}"
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
        "n_samples": len(validator.results),
        "n_skipped_missing": validator.skipped_missing,
        "n_skipped_errors": validator.skipped_errors,
        "require_medical": require_medical,
        "sampling_method": sampling_method,
        "random_seed": random_seed if random_seed is not None else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
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

    # Print summary
    m = report["metrics"]
    print()
    print("=" * 60)
    print("Med-MMHL Validation Results")
    print("=" * 60)
    print(f"Split: {report['split']} | n={report['n_samples']}")
    if "sampling_method" in report:
        print(f"Sampling: {report['sampling_method']}")
        if report.get("random_seed"):
            print(f"Random seed: {report['random_seed']}")
    print()
    print("Pixel Authenticity (rate marked authentic):")
    print(f"  {m['pixel_authenticity']['mean_authentic_rate']:.1%}")
    print()
    print("Veracity (claim plausibility):")
    v_f1 = m['veracity']['f1']
    v_f1_str = f"{v_f1:.3f}" if v_f1 is not None else "N/A"
    print(f"  Accuracy: {m['veracity']['accuracy']:.1%} | F1: {v_f1_str}")
    print()
    print("Alignment (image-claim consistency):")
    a_f1 = m['alignment']['f1']
    a_f1_str = f"{a_f1:.3f}" if a_f1 is not None else "N/A"
    print(f"  Accuracy: {m['alignment']['accuracy']:.1%} | F1: {a_f1_str}")
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
