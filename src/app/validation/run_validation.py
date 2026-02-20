#!/usr/bin/env python3
"""Validate MedContext contextual signals on Med-MMHL using the LangGraph agent.

This is the primary validation runner for comparing MedGemma variants.
Uses the full LangGraph agentic workflow (triage -> tool dispatch -> synthesis)
rather than direct MedGemma calls, for a realistic end-to-end evaluation.

Usage:
  # Run with default settings (n=163, stratified random, seed=42):
  uv run python -m app.validation.run_validation \
    --data-dir data/med-mmhl \
    --output-dir validation_results/med_mmhl_n163_4b_it

  # Quick test with 3 samples:
  uv run python -m app.validation.run_validation \
    --data-dir data/med-mmhl \
    --output-dir validation_results/test_run \
    --limit 3

  # Full test set (no limit):
  uv run python -m app.validation.run_validation \
    --data-dir data/med-mmhl \
    --output-dir validation_results/full_test

Provider selection via environment variables:
  MEDGEMMA_MODEL=google/medgemma-1.1-4b-it ...
  LOCAL_MEDGEMMA_URL=http://localhost:1234 ...
  MEDGEMMA_MODEL=google/medgemma-1.1-4b-pt ...
"""

from __future__ import annotations

import argparse
import json
import random
import signal
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

from app.core.config import settings
from app.validation.chart_generation import generate_charts
from app.validation.loaders import load_med_mmhl_dataset
from app.validation.metrics import (
    bootstrap_confidence_intervals,
    compute_three_dimensional_metrics,
)


def _read_image_bytes(path: Path) -> bytes:
    """Read image file as raw bytes."""
    return path.read_bytes()


def _run_pixel_forensics(image_bytes: bytes) -> dict:
    """Run pixel forensics baseline (ELA/copy-move)."""
    try:
        from app.forensics.service import _run_layer_1

        layer1_result = _run_layer_1(image_bytes)
        return {
            "pixel_authentic": layer1_result.verdict != "MANIPULATED",
            "confidence": layer1_result.confidence,
            "method": "pixel_forensics",
            "layer1_verdict": layer1_result.verdict,
            "layer1_details": layer1_result.details,
        }
    except Exception as e:
        return {
            "pixel_authentic": False,
            "confidence": 0.0,
            "method": "pixel_forensics",
            "error": str(e),
        }


def _extract_contextual_scores(synthesis: dict) -> dict:
    """Extract veracity/alignment scores and categories from LangGraph synthesis output.

    The synthesis output has the structure:
    {
      "part_2": {
        "alignment": "aligned|partially_aligned|misaligned|unclear",
        "confidence": 0.0-1.0,
        "claim_veracity": {
          "factual_accuracy": "accurate|partially_accurate|inaccurate|unverifiable"
        }
      },
      "contextual_integrity": {
        "is_misinformation": bool,
        "claim_veracity": {...},
        "signals": {...}
      }
    }
    """
    # Score mappings
    veracity_map = {
        "accurate": ("true", 0.9),
        "partially_accurate": ("partially_true", 0.6),
        "inaccurate": ("false", 0.1),
        "unverifiable": ("partially_true", 0.5),
    }
    alignment_map = {
        "aligned": ("aligns_fully", 0.9),
        "partially_aligned": ("partially_aligns", 0.6),
        "misaligned": ("does_not_align", 0.1),
        "unclear": ("partially_aligns", 0.5),
    }

    part2 = synthesis.get("part_2", {})
    if not isinstance(part2, dict):
        part2 = {}

    # Extract alignment
    alignment_label = (part2.get("alignment") or "unclear").strip().lower()
    alignment_cat, alignment_score = alignment_map.get(
        alignment_label, ("partially_aligns", 0.5)
    )

    # Adjust alignment score by confidence if available
    confidence = part2.get("confidence")
    if confidence is not None:
        try:
            confidence_val = max(0.0, min(1.0, float(confidence)))
            # Use confidence-weighted score for more nuanced scoring
            alignment_score = alignment_score * confidence_val
        except (TypeError, ValueError):
            pass

    # Extract veracity from claim_veracity
    claim_veracity = part2.get("claim_veracity", {})
    if not isinstance(claim_veracity, dict):
        claim_veracity = {}
    factual_accuracy = (
        (claim_veracity.get("factual_accuracy") or "unverifiable").strip().lower()
    )
    veracity_cat, veracity_score = veracity_map.get(
        factual_accuracy, ("partially_true", 0.5)
    )

    # Extract combined analysis from contextual_integrity
    ci = synthesis.get("contextual_integrity", {})
    is_misinformation = (
        ci.get("is_misinformation", False) if isinstance(ci, dict) else False
    )

    return {
        "veracity_score": veracity_score,
        "veracity_category": veracity_cat,
        "alignment_score": alignment_score,
        "alignment_category": alignment_cat,
        "overall_score": min(veracity_score, alignment_score),
        "is_misinformation": is_misinformation,
        "method": "contextual_analysis",
    }


def _compute_combined_analysis(pixel: dict, contextual: dict, synthesis: dict) -> dict:
    """Combine contextual authenticity with parallel image integrity assessment.

    Keeps pixel forensics and contextual signals as separate sub-assessments
    rather than flat-merging them — pixel integrity tells you whether pixels
    were tampered with, contextual authenticity tells you whether the claim
    is misinformation. These are independent axes.
    """
    ci = synthesis.get("contextual_integrity", {})
    is_misinformation = (
        ci.get("is_misinformation", False) if isinstance(ci, dict) else False
    )

    return {
        "contextual_authenticity": contextual,
        "image_integrity": pixel,
        "method": "combined_analysis",
        "is_misinformation": is_misinformation,
    }


def run_validation(
    data_dir: Path,
    split: str = "test",
    output_dir: Path = Path("validation_results/contextual_signals"),
    limit: int = 163,
    seed: int = 42,
    bootstrap_iterations: int = 0,
) -> dict:
    """Run MedContext validation on Med-MMHL using LangGraph agent."""
    from app.orchestrator.langgraph_agent import MedContextLangGraphAgent

    # Resolve data paths
    benchmark_path = data_dir / "benchmarked_data"
    if not benchmark_path.exists() and (data_dir / "image_article").exists():
        benchmark_path = data_dir
    base_image_dir = data_dir

    # Load dataset
    print(f"Loading Med-MMHL {split} split from {data_dir}...")
    records = load_med_mmhl_dataset(
        benchmark_path=benchmark_path,
        split=split,
        base_image_dir=base_image_dir,
    )
    if not records:
        raise ValueError("No records loaded. Check data_dir path.")

    print(f"Loaded {len(records)} records from {split} split")

    # Stratified random sampling
    if limit and limit < len(records):
        random.seed(seed)
        # Stratified: maintain class balance
        positive = [r for r in records if r["ground_truth"]["is_misinformation"]]
        negative = [r for r in records if not r["ground_truth"]["is_misinformation"]]

        pos_ratio = len(positive) / len(records)
        n_pos = round(limit * pos_ratio)
        n_neg = limit - n_pos

        sampled_pos = random.sample(positive, min(n_pos, len(positive)))
        sampled_neg = random.sample(negative, min(n_neg, len(negative)))
        records = sampled_pos + sampled_neg
        random.shuffle(records)
        sampling_method = f"stratified_random_seed_{seed}"
    else:
        sampling_method = "full_dataset"

    print(f"Validation set: n={len(records)} ({sampling_method})")
    n_misinfo = sum(1 for r in records if r["ground_truth"]["is_misinformation"])
    print(
        f"  Class balance: {n_misinfo} misinformation, {len(records) - n_misinfo} legitimate"
    )

    # Prepare output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write dataset for reproducibility
    dataset_out = []
    for r in records:
        gt = r["ground_truth"]
        dataset_out.append(
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
    with open(output_dir / "med_mmhl_dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset_out, f, indent=2)

    # Initialize LangGraph agent
    print("\nInitializing LangGraph agent...")
    print(f"  MedGemma model: {settings.medgemma_model}")
    print(f"  LLM provider: {settings.llm_provider}")
    print(f"  LLM orchestrator: {settings.llm_orchestrator}")
    agent = MedContextLangGraphAgent()

    # Run inference
    results = []
    skipped_missing = 0
    skipped_errors = 0

    for i, record in enumerate(records):
        image_path = Path(record["image_path"])
        claim = record["claim"]
        image_id = record["image_id"]
        gt = record["ground_truth"]

        print(f"\n[{i+1}/{len(records)}] {image_id}")

        # Read image
        if not image_path.exists():
            print(f"  SKIP: Image not found: {image_path}")
            skipped_missing += 1
            continue

        try:
            image_bytes = _read_image_bytes(image_path)
        except Exception as e:
            print(f"  SKIP: Failed to read image: {e}")
            skipped_missing += 1
            continue

        # Run pixel forensics baseline
        pixel_result = _run_pixel_forensics(image_bytes)

        # Run LangGraph agent with timeout (120s safety net)
        start_time = perf_counter()
        try:
            # Set alarm-based timeout to prevent hangs
            def _timeout_handler(signum, frame):
                raise TimeoutError("agent.run() exceeded 120s timeout")

            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(120)
            try:
                agent_result = agent.run(
                    image_bytes=image_bytes,
                    image_id=image_id,
                    context=claim,
                )
            finally:
                signal.alarm(0)
                signal.signal(signal.SIGALRM, old_handler)

            duration_s = perf_counter() - start_time
            synthesis = agent_result.synthesis or {}
            if not isinstance(synthesis, dict):
                synthesis = {}
            print(f"  OK ({duration_s:.1f}s)")
        except Exception as e:
            duration_s = perf_counter() - start_time
            print(f"  ERROR ({duration_s:.1f}s): {e}")
            traceback.print_exc()
            skipped_errors += 1
            synthesis = {}

        # Extract contextual scores from synthesis
        contextual = _extract_contextual_scores(synthesis)
        combined = _compute_combined_analysis(pixel_result, contextual, synthesis)

        result = {
            "image_id": image_id,
            "claim": claim,
            "ground_truth": {
                "pixel_authentic": gt.get("pixel_authentic", True),
                "alignment": (
                    "misaligned" if gt.get("expected_misalignment") else "aligned"
                ),
                "plausibility": "low" if gt.get("is_fake_claim") else "high",
                "is_misinformation": gt.get("is_fake_claim", False),
            },
            "predictions": {
                "pixel_forensics": pixel_result,
                "contextual_analysis": contextual,
                "combined_analysis": combined,
            },
        }
        results.append(result)

    print(f"\n{'='*60}")
    print(
        f"Inference complete: {len(results)} processed, {skipped_missing} missing, {skipped_errors} errors"
    )

    # Save raw predictions
    with open(output_dir / "raw_predictions.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)

    # Compute metrics
    predictions = []
    ground_truth = []
    for r in results:
        pred = r["predictions"]["contextual_analysis"]
        gt_data = r["ground_truth"]
        predictions.append(
            {
                "pixel_authentic": r["predictions"]["pixel_forensics"].get(
                    "pixel_authentic", True
                ),
                "veracity_score": pred.get("veracity_score", 0.5),
                "alignment_score": pred.get("alignment_score", 0.5),
            }
        )
        ground_truth.append(
            {
                "is_fake_claim": gt_data.get("is_misinformation", False),
                "expected_misalignment": gt_data.get("alignment") == "misaligned",
            }
        )

    metrics = compute_three_dimensional_metrics(predictions, ground_truth)

    if bootstrap_iterations > 0 and len(predictions) >= 10:
        ci = bootstrap_confidence_intervals(
            predictions,
            ground_truth,
            n_iterations=bootstrap_iterations,
        )
        metrics["bootstrap_95ci"] = ci

    # Detect model label from environment
    model_name = output_dir.name
    from app.clinical.medgemma_client import MedGemmaClient

    client = MedGemmaClient()
    provider = client.provider.lower()
    hf_model = settings.medgemma_model

    model_label = "Unknown Model"
    # Provider-based detection first (lmstudio uses default hf_model name)
    if provider in ("lmstudio", "lm_studio", "local") and "quantized" in model_name:
        model_label = "MedGemma 4B Quantized (LM Studio)"
    elif provider in ("lmstudio", "lm_studio"):
        model_label = "MedGemma 4B Quantized (LM Studio)"
    elif "4b-pt" in hf_model or "4b_pt" in model_name:
        model_label = "MedGemma 4B PT (HuggingFace Inference API)"
    elif "4b-it" in hf_model or "4b_it" in model_name:
        model_label = "MedGemma 4B IT (HuggingFace Inference API)"
    elif "4b" in model_name:
        model_label = f"MedGemma 4B ({provider})"

    # Save validation report
    report = {
        "dataset": "Med-MMHL",
        "split": split,
        "model_name": model_name,
        "model_label": model_label,
        "medgemma_provider": provider,
        "medgemma_model": hf_model,
        "llm_orchestrator": settings.llm_orchestrator,
        "llm_worker": settings.llm_worker,
        "n_samples": len(results),
        "n_skipped_missing": skipped_missing,
        "n_skipped_errors": skipped_errors,
        "sampling_method": sampling_method,
        "random_seed": seed,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "classification_info": {
            "veracity": {
                "threshold": 0.5,
                "positive_class": "Plausible (not fake)",
                "negative_class": "Fake claim",
                "decision_rule": "veracity_score > 0.5 = plausible",
                "score_mapping": {"true": 0.9, "partially_true": 0.6, "false": 0.1},
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
                "decision_logic": "VERACITY_FIRST (hierarchical: veracity primary, alignment tiebreaker)",
            },
        },
        "metrics": metrics,
    }

    with open(output_dir / "validation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    # Generate chart data
    try:
        generate_charts(output_dir)
        print(f"\nChart data: {output_dir / 'chart_data.json'}")
    except Exception as chart_err:
        print(f"\nWarning: Chart generation failed: {chart_err}")

    return report


def print_summary(report: dict) -> None:
    """Print a formatted summary of the validation results."""
    m = report["metrics"]
    print()
    print("=" * 60)
    print("Med-MMHL Validation Results")
    print("=" * 60)
    print(f"Model: {report.get('model_label', 'Unknown')}")
    print(f"Provider: {report.get('medgemma_provider', 'unknown')}")
    print(f"MedGemma model: {report.get('medgemma_model', 'unknown')}")
    print(f"Split: {report['split']} | n={report['n_samples']}")
    print(f"Sampling: {report['sampling_method']}")
    if report.get("random_seed") is not None:
        print(f"Random seed: {report['random_seed']}")
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
    print(
        f"Report: {report.get('model_name', 'validation_results')}/validation_report.json"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate MedContext contextual signals on Med-MMHL"
    )
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
        "--output-dir",
        type=Path,
        default=Path("validation_results/contextual_signals"),
        help="Output directory for results",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=163,
        help="Number of samples (default: 163 for stratified n=163)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible sampling (default: 42)",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=0,
        help="Bootstrap iterations for 95%% CI (0=disable)",
    )
    args = parser.parse_args()

    # Validate data directory
    if (
        not (args.data_dir / "benchmarked_data").exists()
        and not (args.data_dir / "image_article").exists()
    ):
        print(f"Error: Data not found at {args.data_dir}")
        print("Run python -m app.validation.download_dataset first to verify setup.")
        return 1

    try:
        report = run_validation(
            data_dir=args.data_dir,
            split=args.split,
            output_dir=args.output_dir,
            limit=args.limit,
            seed=args.seed,
            bootstrap_iterations=args.bootstrap,
        )
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
        return 1

    print_summary(report)
    return 0


if __name__ == "__main__":
    sys.exit(main())
