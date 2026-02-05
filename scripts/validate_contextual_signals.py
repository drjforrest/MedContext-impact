"""Validation script for MedContext contextual signals.

This script validates the four contextual signals (alignment, plausibility,
source reputation, genealogy consistency) against ground truth datasets.

Usage:
    python scripts/validate_contextual_signals.py \
        --dataset data/contextual_signals_v1.json \
        --output-dir validation_results/contextual_signals_v1
"""

from __future__ import annotations

import argparse
import io
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from dotenv import load_dotenv
from PIL import Image, ImageChops
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.utils import resample

# Load environment variables before app imports
load_dotenv(override=True)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.metrics.integrity import compute_contextual_integrity_score  # noqa: E402
from app.orchestrator.agent import MedContextAgent  # noqa: E402
from app.orchestrator.langgraph_agent import MedContextLangGraphAgent  # noqa: E402


class ContextualSignalsValidator:
    """Validates MedContext contextual signals against ground truth."""

    def __init__(
        self,
        dataset_path: Path,
        output_dir: Path,
        agent_type: str = "langgraph",
    ):
        self.dataset_path = dataset_path
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.agent_type = agent_type

        if agent_type == "langgraph":
            self.agent = MedContextLangGraphAgent()
        else:
            self.agent = MedContextAgent()
        self.results: List[Dict[str, Any]] = []

    def load_dataset(self) -> List[Dict[str, Any]]:
        """Load validation dataset with ground truth labels.

        Expected format:
        [
            {
                "image_path": "path/to/image.jpg",
                "claim": "text claim about the image",
                "ground_truth": {
                    "alignment": "aligned" | "misaligned" | "partially_aligned" | "unclear",
                    "plausibility": "high" | "medium" | "low",
                    "is_misinformation": true | false
                }
            },
            ...
        ]
        """
        try:
            with open(self.dataset_path) as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in dataset file: {e}") from e

    def run_validation(self):
        """Execute validation on full dataset."""
        dataset = self.load_dataset()

        print(f"Validating {len(dataset)} image-claim pairs...")
        print(f"Agent: {self.agent_type} ({type(self.agent).__name__})")
        print(f"Dataset: {self.dataset_path}")
        print(f"Output: {self.output_dir}")
        print(f"Started: {datetime.now(timezone.utc).isoformat()}\n")

        for i, item in enumerate(dataset):
            if i % 10 == 0:
                print(f"Progress: {i}/{len(dataset)}")

            # Load image
            image_path = Path(item["image_path"])
            if not image_path.is_absolute():
                # Try relative to dataset file
                image_path = self.dataset_path.parent / image_path

            if not image_path.exists():
                print(f"Warning: Image not found: {image_path}")
                continue

            image_bytes = image_path.read_bytes()

            # Run MedContext agent
            try:
                result = self.agent.run(image_bytes=image_bytes, context=item["claim"])
            except Exception as exc:
                print(f"Error processing {item.get('image_id', i)}: {exc}")
                continue

            # Extract signals and scores
            ci = result.synthesis.get("contextual_integrity", {})
            signals = ci.get("signals", {})

            # Record prediction
            self.results.append(
                {
                    "image_id": item.get("image_id", str(image_path)),
                    "claim": item["claim"],
                    "ground_truth": item["ground_truth"],
                    "predicted": {
                        "alignment": ci.get("alignment"),
                        "alignment_score": signals.get("alignment"),
                        "plausibility_score": signals.get("plausibility"),
                        "genealogy_score": signals.get("genealogy_consistency"),
                        "source_score": signals.get("source_reputation"),
                        "overall_score": ci.get("score"),
                    },
                    "synthesis": result.synthesis,
                }
            )

        print(f"\nValidation complete! Processed {len(self.results)} samples.")
        print(f"Completed: {datetime.now(timezone.utc).isoformat()}\n")

    def compute_metrics(self) -> Dict[str, Any]:
        """Compute evaluation metrics."""
        # Extract ground truth and predictions
        y_true = []
        y_pred = []
        scores = []
        none_score_count = 0

        for result in self.results:
            gt = result["ground_truth"]["alignment"]
            pred = result["predicted"]["alignment"]
            score = result["predicted"]["overall_score"]

            # Binary mapping: aligned vs. not aligned
            y_true.append(1 if gt == "aligned" else 0)
            y_pred.append(1 if pred == "aligned" else 0)
            if score is None:
                none_score_count += 1
            scores.append(score)

        if none_score_count > 0:
            print(
                f"Warning: {none_score_count}/{len(scores)} samples had None scores "
                f"(excluded from ROC-AUC computation)"
            )

        # Filter out None scores for ROC-AUC
        y_true_for_roc = [y for y, s in zip(y_true, scores) if s is not None]
        scores_for_roc = [s for s in scores if s is not None]

        # Compute metrics
        roc_auc = None
        if len(scores_for_roc) > 0 and len(set(y_true_for_roc)) > 1:
            roc_auc = roc_auc_score(y_true_for_roc, scores_for_roc)

        metrics = {
            "accuracy": accuracy_score(y_true, y_pred),
            "precision": precision_score(y_true, y_pred, zero_division=0),
            "recall": recall_score(y_true, y_pred, zero_division=0),
            "f1_score": f1_score(y_true, y_pred, zero_division=0),
            "roc_auc": roc_auc,
            "none_score_count": none_score_count,
        }

        # Bootstrap confidence intervals
        print("Computing bootstrap confidence intervals (1000 iterations)...")
        metrics_with_ci = {}
        for metric_name, metric_fn in [
            ("accuracy", accuracy_score),
            (
                "precision",
                lambda y, p: precision_score(y, p, zero_division=0),
            ),
            ("recall", lambda y, p: recall_score(y, p, zero_division=0)),
            ("f1_score", lambda y, p: f1_score(y, p, zero_division=0)),
        ]:
            ci = self.bootstrap_metric(y_true, y_pred, metric_fn)
            metrics_with_ci[metric_name] = ci

        # ROC AUC bootstrap (using filtered scores without None values)
        if metrics["roc_auc"] is not None:
            roc_ci = self.bootstrap_metric(
                y_true_for_roc, scores_for_roc, lambda y, s: roc_auc_score(y, s)
            )
            metrics_with_ci["roc_auc"] = roc_ci

        return {
            "metrics": metrics,
            "metrics_with_ci": metrics_with_ci,
            "confusion_matrix": confusion_matrix(y_true, y_pred).tolist(),
            "classification_report": classification_report(
                y_true,
                y_pred,
                target_names=["misaligned", "aligned"],
                output_dict=True,
            ),
        }

    def bootstrap_metric(
        self, y_true, y_pred, metric_fn, n_iterations=1000
    ) -> Dict[str, Any]:
        """Compute 95% CI via bootstrap."""
        scores = []
        for i in range(n_iterations):
            indices = resample(range(len(y_true)), random_state=i)
            y_true_sample = [y_true[i] for i in indices]
            y_pred_sample = [y_pred[i] for i in indices]

            try:
                score = metric_fn(y_true_sample, y_pred_sample)
                scores.append(score)
            except ValueError:
                # Handle cases where resampling creates all-one-class
                continue

        if not scores:
            print("Warning: Bootstrap produced no valid scores — returning None values")
            return {"mean": None, "lower_ci": None, "upper_ci": None}

        return {
            "mean": float(np.mean(scores)),
            "lower_ci": float(np.percentile(scores, 2.5)),
            "upper_ci": float(np.percentile(scores, 97.5)),
        }

    def analyze_signals(self) -> Dict[str, Any]:
        """Analyze individual signal performance."""
        signal_analysis = {}

        for signal_name in [
            "alignment_score",
            "plausibility_score",
            "genealogy_score",
            "source_score",
        ]:
            # Extract signal values
            y_true = []
            signal_values = []

            for result in self.results:
                gt = result["ground_truth"]["alignment"]
                signal_val = result["predicted"].get(signal_name)

                if signal_val is not None:
                    y_true.append(1 if gt == "aligned" else 0)
                    signal_values.append(signal_val)

            if len(signal_values) > 0 and len(set(y_true)) > 1:
                # Compute ROC AUC for this signal alone
                try:
                    roc_auc = roc_auc_score(y_true, signal_values)
                except ValueError:
                    roc_auc = None

                # Compute mean difference between aligned vs. misaligned
                aligned_vals = [s for s, t in zip(signal_values, y_true) if t == 1]
                misaligned_vals = [s for s, t in zip(signal_values, y_true) if t == 0]

                signal_analysis[signal_name] = {
                    "roc_auc": roc_auc,
                    "mean_aligned": (
                        float(np.mean(aligned_vals)) if aligned_vals else None
                    ),
                    "mean_misaligned": (
                        float(np.mean(misaligned_vals)) if misaligned_vals else None
                    ),
                    "separation": (
                        float(np.mean(aligned_vals) - np.mean(misaligned_vals))
                        if aligned_vals and misaligned_vals
                        else None
                    ),
                    "coverage": len(signal_values) / len(self.results),
                }

        return signal_analysis

    def ablation_study(self) -> Dict[str, Any]:
        """Measure contribution of each signal via ablation."""
        # Baseline: All signals
        y_true = []
        y_pred_baseline = []

        for result in self.results:
            gt = result["ground_truth"]["alignment"]
            score = result["predicted"]["overall_score"]

            y_true.append(1 if gt == "aligned" else 0)
            y_pred_baseline.append(1 if score >= 0.5 else 0)

        baseline_acc = accuracy_score(y_true, y_pred_baseline)

        # Ablation: Remove each signal
        print("Running ablation study...")
        ablation_results = {"baseline": baseline_acc}

        for signal_to_remove in [
            "alignment",
            "plausibility",
            "genealogy",
            "source",
        ]:
            y_pred_ablated = []

            for result in self.results:
                signals = result["predicted"]

                # Recompute score without this signal
                signal_values = {
                    "alignment": signals.get("alignment_score"),
                    "plausibility": signals.get("plausibility_score"),
                    "genealogy_consistency": signals.get("genealogy_score"),
                    "source_reputation": signals.get("source_score"),
                }

                # Set removed signal to None
                if signal_to_remove == "alignment":
                    signal_values["alignment"] = None
                elif signal_to_remove == "plausibility":
                    signal_values["plausibility"] = None
                elif signal_to_remove == "genealogy":
                    signal_values["genealogy_consistency"] = None
                elif signal_to_remove == "source":
                    signal_values["source_reputation"] = None

                # Recompute score (weights will auto-adjust)
                ablated_score = compute_contextual_integrity_score(**signal_values)
                y_pred_ablated.append(1 if ablated_score >= 0.5 else 0)

            ablated_acc = accuracy_score(y_true, y_pred_ablated)
            contribution = baseline_acc - ablated_acc

            ablation_results[f"without_{signal_to_remove}"] = {
                "accuracy": ablated_acc,
                "contribution": contribution,
            }

        return ablation_results

    def pixel_forensics_baseline(self) -> Dict[str, Any]:
        """Run pixel forensics (ELA + EXIF) on the same dataset as a baseline.

        This provides an apples-to-apples comparison: both methods evaluated
        on the exact same images with the same ground truth labels.

        Pixel forensics can only analyze the image — it has no access to the
        claim text. It predicts AUTHENTIC or MANIPULATED based on pixel-level
        artifacts. Since medical misinformation typically uses real (untampered)
        images with false claims, pixel forensics should perform at or near
        chance level on this task.
        """
        print("Running pixel forensics baseline on same dataset...")
        dataset = self.load_dataset()

        # Cache ELA results per image path (same image appears with multiple claims)
        ela_cache: Dict[str, Dict[str, Any]] = {}

        y_true = []
        y_pred = []
        ela_scores = []
        per_image_results = []

        for item in dataset:
            image_path = str(Path(item["image_path"]))
            gt = item["ground_truth"]["alignment"]
            y_true.append(1 if gt == "aligned" else 0)

            if image_path not in ela_cache:
                ela_cache[image_path] = self._run_ela(image_path)

            ela_result = ela_cache[image_path]

            # Map pixel forensics verdict to alignment prediction:
            # AUTHENTIC → predict "aligned" (image looks real, claim might match)
            # MANIPULATED → predict "misaligned" (image looks tampered)
            # UNCERTAIN → predict "aligned" (benefit of the doubt)
            verdict = ela_result["verdict"]
            if verdict == "MANIPULATED":
                y_pred.append(0)  # misaligned
            else:
                y_pred.append(1)  # aligned

            ela_scores.append(ela_result["score"])
            per_image_results.append(
                {
                    "image_id": item.get("image_id", image_path),
                    "claim": item["claim"],
                    "ground_truth_alignment": gt,
                    "ela_verdict": verdict,
                    "ela_score": ela_result["score"],
                    "ela_std": ela_result["ela_std"],
                    "predicted_alignment": (
                        "aligned" if verdict != "MANIPULATED" else "misaligned"
                    ),
                }
            )

        acc = accuracy_score(y_true, y_pred)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        f1 = f1_score(y_true, y_pred, zero_division=0)

        roc_auc = None
        if len(set(y_true)) > 1:
            try:
                roc_auc = roc_auc_score(y_true, ela_scores)
            except ValueError:
                pass

        # Bootstrap CI for accuracy
        acc_ci = self.bootstrap_metric(y_true, y_pred, accuracy_score)

        # Count verdict distribution
        verdicts = [r["ela_verdict"] for r in per_image_results]
        from collections import Counter

        verdict_dist = dict(Counter(verdicts))

        return {
            "metrics": {
                "accuracy": acc,
                "precision": prec,
                "recall": rec,
                "f1_score": f1,
                "roc_auc": roc_auc,
            },
            "accuracy_ci": acc_ci,
            "verdict_distribution": verdict_dist,
            "unique_images_analyzed": len(ela_cache),
            "total_pairs": len(dataset),
            "per_image_results": per_image_results,
        }

    def _run_ela(self, image_path: str) -> Dict[str, Any]:
        """Run Error Level Analysis on a single image.

        Recompresses at JPEG quality 95 and measures pixel differences.
        High ELA variance suggests manipulation; low variance suggests authentic.
        """
        try:
            original = Image.open(image_path)
            if original.mode not in ("RGB", "L"):
                original = original.convert("RGB")

            temp_buffer = io.BytesIO()
            original.save(temp_buffer, format="JPEG", quality=95)
            temp_buffer.seek(0)
            compressed = Image.open(temp_buffer)

            ela_image = ImageChops.difference(original, compressed)
            ela_gray = ela_image.convert("L")
            ela_array = np.array(ela_gray, dtype=np.float32)

            # Normalize ELA
            ela_max_raw = float(np.max(ela_array)) if ela_array.size else 0.0
            if ela_max_raw > 0:
                ela_array = ela_array * (255.0 / ela_max_raw)

            ela_std = float(np.std(ela_array))

            # Threshold: higher std → more likely manipulated
            # Use the same default thresholds as validate_forensics.py
            std_authentic = 0.22
            std_manipulated = 0.74
            if std_manipulated > std_authentic:
                score = (ela_std - std_authentic) / (std_manipulated - std_authentic)
                score = max(0.0, min(1.0, score))
            else:
                score = 0.5

            verdict = "MANIPULATED" if score >= 0.5 else "AUTHENTIC"

            return {
                "verdict": verdict,
                "score": score,
                "ela_std": ela_std,
                "confidence": max(score, 1.0 - score),
            }
        except Exception as exc:
            return {
                "verdict": "UNCERTAIN",
                "score": 0.5,
                "ela_std": 0.0,
                "confidence": 0.5,
                "error": str(exc),
            }

    def generate_report(self):
        """Generate comprehensive validation report."""
        print("Generating validation report...")

        metrics = self.compute_metrics()
        signal_analysis = self.analyze_signals()
        ablation = self.ablation_study()
        pixel_baseline = self.pixel_forensics_baseline()

        report = {
            "metadata": {
                "dataset_path": str(self.dataset_path),
                "n_samples": len(self.results),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "version": "2.0",
                "agent_type": self.agent_type,
                "agent_class": type(self.agent).__name__,
            },
            "overall_performance": metrics,
            "pixel_forensics_baseline": pixel_baseline,
            "signal_analysis": signal_analysis,
            "ablation_study": ablation,
            "raw_results": self.results,
        }

        # Save report
        report_path = self.output_dir / "contextual_signals_validation_report.json"
        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        # Print summary
        ctx_acc = metrics["metrics"]["accuracy"]
        pf_acc = pixel_baseline["metrics"]["accuracy"]
        improvement = ctx_acc - pf_acc

        print(f"\n{'=' * 70}")
        print("CONTEXTUAL SIGNALS VALIDATION REPORT (v2.0)")
        print(f"{'=' * 70}\n")

        print(f"Dataset: {len(self.results)} samples (same for both methods)\n")

        print("--- PIXEL FORENSICS BASELINE (same images) ---")
        print(f"  accuracy:         {pf_acc:.3f}", end="")
        pf_ci = pixel_baseline["accuracy_ci"]
        if pf_ci["mean"] is not None:
            print(f" [{pf_ci['lower_ci']:.3f}, {pf_ci['upper_ci']:.3f}]")
        else:
            print()
        print(f"  verdict dist:     {pixel_baseline['verdict_distribution']}")
        print(f"  unique images:    {pixel_baseline['unique_images_analyzed']}")
        pf_roc = pixel_baseline["metrics"]["roc_auc"]
        if pf_roc is not None:
            print(f"  roc_auc:          {pf_roc:.3f}")
        print()

        print(
            f"--- CONTEXTUAL SIGNALS ({self.agent_type} / {type(self.agent).__name__}) ---"
        )
        print("Overall Performance (with 95% CI):")
        for metric, values in metrics["metrics_with_ci"].items():
            if values["mean"] is not None:
                print(
                    f"  {metric:15s}: {values['mean']:.3f} "
                    f"[{values['lower_ci']:.3f}, {values['upper_ci']:.3f}]"
                )
            else:
                print(f"  {metric:15s}: N/A")

        print("\n--- HEAD-TO-HEAD COMPARISON (same dataset) ---")
        print(f"  Pixel forensics accuracy:     {pf_acc:.3f}")
        print(f"  Contextual signals accuracy:  {ctx_acc:.3f}")
        print(
            f"  Improvement:                  {improvement:+.3f} ({improvement / max(pf_acc, 0.001) * 100:+.1f}% relative)"
        )

        print("\nSignal Analysis (Individual ROC AUC):")
        for signal, analysis in signal_analysis.items():
            if analysis["roc_auc"] is not None:
                print(
                    f"  {signal:25s}: {analysis['roc_auc']:.3f} "
                    f"(coverage: {analysis['coverage']:.1%})"
                )

        print("\nAblation Study (Signal Contribution):")
        for key, value in ablation.items():
            if key == "baseline":
                print(f"  {key:25s}: {value:.3f}")
            else:
                print(
                    f"  {key:25s}: {value['accuracy']:.3f} "
                    f"(contribution: {value['contribution']:+.3f})"
                )

        print(f"\nFull report saved to: {report_path}")
        print(f"{'=' * 70}\n")

        return report


def main():
    parser = argparse.ArgumentParser(
        description="Validate MedContext contextual signals"
    )
    parser.add_argument(
        "--dataset",
        type=Path,
        required=True,
        help="Path to validation dataset JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("validation_results/contextual_signals"),
        help="Output directory for results",
    )
    parser.add_argument(
        "--agent",
        choices=["langgraph", "deterministic"],
        default="langgraph",
        help="Agent implementation to use (default: langgraph)",
    )

    args = parser.parse_args()

    if not args.dataset.exists():
        print(f"Error: Dataset not found: {args.dataset}")
        sys.exit(1)

    validator = ContextualSignalsValidator(
        dataset_path=args.dataset,
        output_dir=args.output_dir,
        agent_type=args.agent,
    )

    validator.run_validation()
    validator.generate_report()


if __name__ == "__main__":
    main()
