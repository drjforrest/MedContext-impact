#!/usr/bin/env python3
"""
Forensics Validation Script - Compute Confidence Intervals

This script validates the deepfake detection forensics implementation against
public medical deepfake datasets and computes statistical confidence intervals.

Datasets Supported:
1. MedFake: Medical Image Deepfake Dataset (Kaggle)
2. FakeMed: Synthetic Medical Image Detection Challenge
3. Custom dataset (place in data/validation/)

Usage:
    python scripts/validate_forensics.py --dataset medifake --bootstrap 1000

Requirements:
    pip install scipy scikit-learn pandas seaborn matplotlib
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import io

import numpy as np
from scipy import stats
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, confusion_matrix, roc_curve
)
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.clinical.medgemma_client import (
    MedGemmaClient,
    MedGemmaClientError,
    MedGemmaResult,
)
from app.forensics.deepfake import (
    run_deepfake_detection,
    run_layer_1,
    run_layer_3,
    DeepfakeEnsembleResult,
    DeepfakeLayerResult,
)

DEFAULT_MEDGEMMA_PROMPT = (
    "You are a medical image forensics assistant. "
    "Assess whether the image is authentic or manipulated. "
    "Return JSON with keys: verdict (AUTHENTIC|MANIPULATED|UNCERTAIN), "
    "confidence (0-1), rationale."
)


class ForensicsValidator:
    """Validates forensics detection with confidence intervals."""

    def __init__(
        self,
        dataset_path: Path,
        bootstrap_iterations: int = 1000,
        balance: bool = False,
        seed: int = 42,
        prediction_mode: str = "ensemble",
        use_medgemma: bool = False,
        medgemma_prompt: str | None = None,
    ):
        self.dataset_path = dataset_path
        self.bootstrap_iterations = bootstrap_iterations
        self.balance = balance
        self.seed = seed
        self.prediction_mode = prediction_mode
        self.use_medgemma = use_medgemma
        self.medgemma_prompt = medgemma_prompt or DEFAULT_MEDGEMMA_PROMPT
        self._medgemma_client = MedGemmaClient() if use_medgemma else None
        self.medgemma_stats = {
            "calls": 0,
            "errors": 0,
            "uncertain": 0,
            "error_samples": [],
        }
        self.results: List[Dict] = []

    def load_dataset(self) -> Tuple[List[bytes], List[str]]:
        """
        Load validation dataset with support for multiple formats.

        Supports:
        1. Generic structure (authentic/ and manipulated/ subdirs)
        2. MedForensics structure (real/ and fake/ subdirs with modality subdirs)
        3. BTD structure (original/ and tampered/ with metadata)
        4. UCI structure (scans with labels.csv)

        Returns:
            Tuple of (image_bytes_list, ground_truth_labels)
        """
        print(f"📂 Loading dataset from {self.dataset_path}")

        # Auto-detect dataset format
        if (self.dataset_path / "real").exists() and (self.dataset_path / "fake").exists():
            images, labels = self._load_medforensics_format()
        elif (self.dataset_path / "original").exists() and (self.dataset_path / "tampered").exists():
            images, labels = self._load_btd_format()
        elif (self.dataset_path / "labels.csv").exists():
            images, labels = self._load_uci_format()
        else:
            images, labels = self._load_generic_format()

        if self.balance:
            images, labels = self._balance_dataset(images, labels)

        return images, labels

    def _load_generic_format(self) -> Tuple[List[bytes], List[str]]:
        """Load generic authentic/manipulated structure."""
        images = []
        labels = []

        # Load authentic images
        authentic_dir = self.dataset_path / "authentic"
        if authentic_dir.exists():
            for img_path in list(authentic_dir.glob("*.jpg")) + list(authentic_dir.glob("*.png")):
                with open(img_path, "rb") as f:
                    images.append(f.read())
                    labels.append("AUTHENTIC")
            print(f"  ✓ Loaded {len([l for l in labels if l == 'AUTHENTIC'])} authentic images")

        # Load manipulated images
        manipulated_dir = self.dataset_path / "manipulated"
        if manipulated_dir.exists():
            for img_path in list(manipulated_dir.glob("*.jpg")) + list(manipulated_dir.glob("*.png")):
                with open(img_path, "rb") as f:
                    images.append(f.read())
                    labels.append("MANIPULATED")
            print(f"  ✓ Loaded {len([l for l in labels if l == 'MANIPULATED'])} manipulated images")

        if not images:
            raise ValueError(f"No images found in {self.dataset_path}")

        return images, labels

    def _load_medforensics_format(self) -> Tuple[List[bytes], List[str]]:
        """
        Load MedForensics dataset format.

        Structure:
            real/
                ultrasound/
                endoscopy/
                ...
            fake/
                ultrasound_gan/
                endoscopy_sd/
                ...
        """
        print("  📦 Detected MedForensics format")
        images = []
        labels = []

        # Load real images from all modality subdirs
        real_dir = self.dataset_path / "real"
        if real_dir.exists():
            for modality_dir in real_dir.iterdir():
                if modality_dir.is_dir():
                    for img_path in list(modality_dir.glob("*.jpg")) + list(modality_dir.glob("*.png")):
                        with open(img_path, "rb") as f:
                            images.append(f.read())
                            labels.append("AUTHENTIC")
            print(f"  ✓ Loaded {len([l for l in labels if l == 'AUTHENTIC'])} real images")

        # Load fake images from all modality subdirs
        fake_dir = self.dataset_path / "fake"
        if fake_dir.exists():
            for modality_dir in fake_dir.iterdir():
                if modality_dir.is_dir():
                    for img_path in list(modality_dir.glob("*.jpg")) + list(modality_dir.glob("*.png")):
                        with open(img_path, "rb") as f:
                            images.append(f.read())
                            labels.append("MANIPULATED")
            print(f"  ✓ Loaded {len([l for l in labels if l == 'MANIPULATED'])} fake images")

        return images, labels

    def _load_btd_format(self) -> Tuple[List[bytes], List[str]]:
        """
        Load Back-in-Time Diffusion dataset format.

        Structure:
            original/
                scan_001.png
                scan_002.png
            tampered/
                scan_001_tampered.png
                scan_002_tampered.png
        """
        print("  📦 Detected BTD format")
        images = []
        labels = []

        # Load original images
        original_dir = self.dataset_path / "original"
        if original_dir.exists():
            for img_path in list(original_dir.glob("*.jpg")) + list(original_dir.glob("*.png")):
                with open(img_path, "rb") as f:
                    images.append(f.read())
                    labels.append("AUTHENTIC")
            print(f"  ✓ Loaded {len([l for l in labels if l == 'AUTHENTIC'])} original images")

        # Load tampered images
        tampered_dir = self.dataset_path / "tampered"
        if tampered_dir.exists():
            for img_path in list(tampered_dir.glob("*.jpg")) + list(tampered_dir.glob("*.png")):
                with open(img_path, "rb") as f:
                    images.append(f.read())
                    labels.append("MANIPULATED")
            print(f"  ✓ Loaded {len([l for l in labels if l == 'MANIPULATED'])} tampered images")

        return images, labels

    def _load_uci_format(self) -> Tuple[List[bytes], List[str]]:
        """
        Load UCI Medical Image Tamper Detection format.

        Structure:
            images/
                scan_001.png
                scan_002.png
            labels.csv (scan_id, is_tampered)
        """
        print("  📦 Detected UCI format")
        import csv

        images = []
        labels = []

        # Read labels
        labels_file = self.dataset_path / "labels.csv"
        label_map = {}
        with open(labels_file, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                scan_id = row.get("scan_id") or row.get("image_id")
                is_tampered = row.get("is_tampered") or row.get("label")
                label_map[scan_id] = "MANIPULATED" if is_tampered in ["1", "true", "True", "tampered"] else "AUTHENTIC"

        # Load images
        images_dir = self.dataset_path / "images"
        if images_dir.exists():
            for img_path in list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png")):
                scan_id = img_path.stem
                if scan_id in label_map:
                    with open(img_path, "rb") as f:
                        images.append(f.read())
                        labels.append(label_map[scan_id])

        print(f"  ✓ Loaded {len(images)} images with labels")
        print(f"    - Authentic: {len([l for l in labels if l == 'AUTHENTIC'])}")
        print(f"    - Manipulated: {len([l for l in labels if l == 'MANIPULATED'])}")

        return images, labels

    def _balance_dataset(
        self, images: List[bytes], labels: List[str]
    ) -> Tuple[List[bytes], List[str]]:
        """Balance dataset by undersampling to the minority class size."""
        if not images:
            return images, labels

        indices_auth = [i for i, label in enumerate(labels) if label == "AUTHENTIC"]
        indices_man = [i for i, label in enumerate(labels) if label == "MANIPULATED"]

        if not indices_auth or not indices_man:
            print("  ⚠️  Cannot balance dataset (single class present).")
            return images, labels

        min_count = min(len(indices_auth), len(indices_man))
        rng = np.random.default_rng(self.seed)

        sampled_auth = rng.choice(indices_auth, size=min_count, replace=False)
        sampled_man = rng.choice(indices_man, size=min_count, replace=False)
        sampled_indices = np.concatenate([sampled_auth, sampled_man])
        rng.shuffle(sampled_indices)

        balanced_images = [images[i] for i in sampled_indices]
        balanced_labels = [labels[i] for i in sampled_indices]

        print(
            f"  ⚖️  Balanced dataset to {min_count} authentic + {min_count} manipulated"
        )
        return balanced_images, balanced_labels

    def run_predictions(self, images: List[bytes]) -> List[DeepfakeEnsembleResult]:
        """Run forensics detection on all images."""
        print(f"\n🔍 Running forensics detection on {len(images)} images...")

        predictions = []
        for idx, img_bytes in enumerate(images):
            if (idx + 1) % 10 == 0:
                print(f"  Progress: {idx + 1}/{len(images)}")

            try:
                if self.use_medgemma:
                    layer_1 = run_layer_1(img_bytes)
                    layer_2 = self._run_medgemma_layer(img_bytes)
                    layer_3 = run_layer_3(img_bytes)
                    self.medgemma_stats["calls"] += 1
                    if layer_2.verdict == "UNCERTAIN":
                        self.medgemma_stats["uncertain"] += 1
                    if "error" in layer_2.details:
                        self.medgemma_stats["errors"] += 1
                        if len(self.medgemma_stats["error_samples"]) < 5:
                            self.medgemma_stats["error_samples"].append(
                                str(layer_2.details.get("error", "unknown_error"))
                            )
                    result = self._ensemble_from_layers(layer_1, layer_2, layer_3)
                else:
                    result = run_deepfake_detection(img_bytes)
                predictions.append(result)
            except Exception as e:
                print(f"  ⚠️  Error on image {idx}: {e}")
                # Create a fallback result
                fallback_layer = DeepfakeLayerResult(
                    verdict="UNCERTAIN",
                    confidence=0.5,
                    details={"error": str(e), "source": "validation_fallback"},
                )
                predictions.append(DeepfakeEnsembleResult(
                    final_verdict="UNCERTAIN",
                    confidence=0.5,
                    layer_1=fallback_layer,
                    layer_2=fallback_layer,
                    layer_3=fallback_layer,
                ))

        print(f"  ✓ Completed {len(predictions)} predictions")
        return predictions

    def _ensemble_from_layers(
        self,
        layer_1: DeepfakeLayerResult,
        layer_2: DeepfakeLayerResult,
        layer_3: DeepfakeLayerResult,
    ) -> DeepfakeEnsembleResult:
        verdicts = [layer_1.verdict, layer_2.verdict, layer_3.verdict]
        non_uncertain = [v for v in verdicts if v != "UNCERTAIN"]

        if not non_uncertain:
            final_verdict = "UNCERTAIN"
            confidence = 0.5
        else:
            authentic_votes = non_uncertain.count("AUTHENTIC")
            manipulated_votes = non_uncertain.count("MANIPULATED")

            if authentic_votes > manipulated_votes:
                final_verdict = "AUTHENTIC"
                if authentic_votes == 3:
                    confidence = 0.90
                elif authentic_votes == 2:
                    confidence = 0.75
                else:
                    confidence = 0.60
            elif manipulated_votes > authentic_votes:
                final_verdict = "MANIPULATED"
                if manipulated_votes == 3:
                    confidence = 0.90
                elif manipulated_votes == 2:
                    confidence = 0.75
                else:
                    confidence = 0.60
            else:
                final_verdict = "UNCERTAIN"
                confidence = 0.50

            avg_confidence = sum(
                layer.confidence
                for layer in [layer_1, layer_2, layer_3]
                if layer.verdict == final_verdict
            ) / max(
                1,
                sum(
                    1
                    for layer in [layer_1, layer_2, layer_3]
                    if layer.verdict == final_verdict
                ),
            )
            confidence = min(confidence, avg_confidence * 1.1)

        return DeepfakeEnsembleResult(
            final_verdict=final_verdict,
            confidence=round(confidence, 2),
            layer_1=layer_1,
            layer_2=layer_2,
            layer_3=layer_3,
        )

    def _run_medgemma_layer(self, image_bytes: bytes) -> DeepfakeLayerResult:
        if self._medgemma_client is None:
            return DeepfakeLayerResult(
                verdict="UNCERTAIN",
                confidence=0.5,
                details={"error": "MedGemma not enabled", "method": "medgemma"},
            )
        try:
            result = self._medgemma_client.analyze_image(
                image_bytes=image_bytes,
                prompt=self.medgemma_prompt,
            )
        except MedGemmaClientError as exc:
            return DeepfakeLayerResult(
                verdict="UNCERTAIN",
                confidence=0.5,
                details={"error": str(exc), "method": "medgemma"},
            )

        verdict, confidence, details = self._parse_medgemma_result(result)
        return DeepfakeLayerResult(
            verdict=verdict,
            confidence=confidence,
            details={
                "method": "medgemma",
                "provider": result.provider,
                "model": result.model,
                "parsed": details,
                "raw_text": (result.raw_text or "")[:1000],
                "output_type": type(result.output).__name__,
            },
        )

    def _parse_medgemma_result(
        self, result: MedGemmaResult
    ) -> tuple[str, float, dict]:
        output = result.output
        raw_text = result.raw_text or ""
        parsed: dict[str, object] = {}

        if isinstance(output, dict):
            parsed = output
        elif isinstance(output, list) and output:
            first = output[0]
            if isinstance(first, dict):
                parsed = first

        text_candidate = ""
        if isinstance(parsed, dict):
            text_candidate = str(parsed.get("text") or parsed.get("generated_text") or "")
        if not text_candidate:
            text_candidate = raw_text
        if not text_candidate and output:
            text_candidate = str(output)

        json_candidate = None
        if isinstance(parsed, dict) and any(key in parsed for key in ("verdict", "confidence")):
            json_candidate = parsed
        else:
            match = re.search(r"\{.*\}", text_candidate, flags=re.DOTALL)
            if match:
                try:
                    json_candidate = json.loads(match.group(0))
                except json.JSONDecodeError:
                    json_candidate = None

        verdict = None
        confidence = None
        if isinstance(json_candidate, dict):
            verdict = json_candidate.get("verdict")
            confidence = json_candidate.get("confidence")
            parsed = json_candidate

        verdict_str = str(verdict or "").strip().upper()
        if verdict_str not in {"AUTHENTIC", "MANIPULATED", "UNCERTAIN"}:
            text_lower = (text_candidate or "").lower()
            if any(token in text_lower for token in ("manipulated", "tampered", "fake")):
                verdict_str = "MANIPULATED"
            elif any(token in text_lower for token in ("authentic", "real", "genuine")):
                verdict_str = "AUTHENTIC"
            else:
                verdict_str = "UNCERTAIN"

        try:
            confidence_val = float(confidence) if confidence is not None else 0.5
        except (TypeError, ValueError):
            confidence_val = 0.5

        confidence_val = max(0.0, min(1.0, confidence_val))
        return verdict_str, confidence_val, parsed

    def compute_metrics(
        self,
        ground_truth: List[str],
        predictions: List[DeepfakeEnsembleResult]
    ) -> Dict[str, float]:
        """Compute classification metrics."""
        def select_prediction(pred: DeepfakeEnsembleResult) -> tuple[str, float]:
            if self.prediction_mode == "layer_1":
                return pred.layer_1.verdict, pred.layer_1.confidence
            if self.prediction_mode == "layer_2":
                return pred.layer_2.verdict, pred.layer_2.confidence
            if self.prediction_mode == "layer_3":
                return pred.layer_3.verdict, pred.layer_3.confidence
            return pred.final_verdict, pred.confidence

        # Convert to binary: MANIPULATED=1, AUTHENTIC=0, UNCERTAIN=0.5 → round to nearest
        y_true = [1 if label == "MANIPULATED" else 0 for label in ground_truth]
        y_pred_labels = [
            (
                1
                if select_prediction(pred)[0] == "MANIPULATED"
                else 0
                if select_prediction(pred)[0] == "AUTHENTIC"
                else (1 if select_prediction(pred)[1] > 0.5 else 0)
            )
            for pred in predictions
        ]
        y_pred_scores = [select_prediction(pred)[1] for pred in predictions]

        return {
            "accuracy": accuracy_score(y_true, y_pred_labels),
            "precision": precision_score(y_true, y_pred_labels, zero_division=0),
            "recall": recall_score(y_true, y_pred_labels, zero_division=0),
            "f1_score": f1_score(y_true, y_pred_labels, zero_division=0),
            "roc_auc": roc_auc_score(y_true, y_pred_scores) if len(set(y_true)) > 1 else 0.5,
        }

    def bootstrap_confidence_intervals(
        self,
        ground_truth: List[str],
        predictions: List[DeepfakeEnsembleResult],
        alpha: float = 0.05
    ) -> Dict[str, Tuple[float, float, float]]:
        """
        Compute bootstrap confidence intervals for metrics.

        Returns:
            Dict with metric_name: (mean, lower_ci, upper_ci)
        """
        print(f"\n📊 Computing bootstrap confidence intervals ({self.bootstrap_iterations} iterations)...")

        n = len(ground_truth)
        bootstrap_metrics = {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1_score": [],
            "roc_auc": []
        }

        for i in range(self.bootstrap_iterations):
            if (i + 1) % 100 == 0:
                print(f"  Bootstrap iteration {i + 1}/{self.bootstrap_iterations}")

            # Resample with replacement
            indices = np.random.choice(n, size=n, replace=True)
            resampled_truth = [ground_truth[i] for i in indices]
            resampled_preds = [predictions[i] for i in indices]

            # Compute metrics on resampled data
            metrics = self.compute_metrics(resampled_truth, resampled_preds)
            for key, value in metrics.items():
                bootstrap_metrics[key].append(value)

        # Compute confidence intervals
        confidence_intervals = {}
        for metric_name, values in bootstrap_metrics.items():
            values_array = np.array(values)
            mean = np.mean(values_array)
            lower = np.percentile(values_array, 100 * alpha / 2)
            upper = np.percentile(values_array, 100 * (1 - alpha / 2))
            confidence_intervals[metric_name] = (mean, lower, upper)

        print("  ✓ Bootstrap completed")
        return confidence_intervals

    def analyze_layer_thresholds(
        self,
        images: List[bytes],
        ground_truth: List[str]
    ) -> Dict:
        """
        Analyze ELA thresholds to determine optimal values.

        Returns optimal thresholds based on ROC analysis.
        """
        print("\n🎯 Analyzing ELA thresholds...")

        ela_stats = {"authentic": [], "manipulated": []}
        ela_failures = 0

        for img_bytes, label in zip(images, ground_truth):
            try:
                layer_1_result = run_layer_1(img_bytes)
                ela_metrics = {
                    "ela_mean": layer_1_result.details.get("ela_mean"),
                    "ela_std": layer_1_result.details.get("ela_std"),
                    "ela_max": layer_1_result.details.get("ela_max"),
                }

                if all(value is not None for value in ela_metrics.values()):
                    category = "authentic" if label == "AUTHENTIC" else "manipulated"
                    ela_stats[category].append(ela_metrics)
            except Exception as e:
                ela_failures += 1
                continue

        if not ela_stats["authentic"] or not ela_stats["manipulated"]:
            print("  ⚠️  ELA metrics missing for one or both classes.")
        if ela_failures:
            print(f"  ⚠️  ELA failed on {ela_failures} images.")

        # Compute statistics
        threshold_analysis = {
            "authentic_ela_std": {
                "mean": np.mean([m["ela_std"] for m in ela_stats["authentic"]]) if ela_stats["authentic"] else 0,
                "median": np.median([m["ela_std"] for m in ela_stats["authentic"]]) if ela_stats["authentic"] else 0,
                "std": np.std([m["ela_std"] for m in ela_stats["authentic"]]) if ela_stats["authentic"] else 0,
            },
            "manipulated_ela_std": {
                "mean": np.mean([m["ela_std"] for m in ela_stats["manipulated"]]) if ela_stats["manipulated"] else 0,
                "median": np.median([m["ela_std"] for m in ela_stats["manipulated"]]) if ela_stats["manipulated"] else 0,
                "std": np.std([m["ela_std"] for m in ela_stats["manipulated"]]) if ela_stats["manipulated"] else 0,
            },
            "recommended_thresholds": {}
        }

        # Compute optimal threshold using Youden's J statistic
        if ela_stats["authentic"] and ela_stats["manipulated"]:
            all_ela_stds = [m["ela_std"] for m in ela_stats["authentic"] + ela_stats["manipulated"]]
            all_labels = [0] * len(ela_stats["authentic"]) + [1] * len(ela_stats["manipulated"])

            if len(set(all_labels)) > 1:
                fpr, tpr, thresholds = roc_curve(all_labels, all_ela_stds)
                optimal_idx = np.argmax(tpr - fpr)  # Youden's J
                optimal_threshold = thresholds[optimal_idx]

                threshold_analysis["recommended_thresholds"]["ela_std_manipulated"] = float(optimal_threshold)
                threshold_analysis["recommended_thresholds"]["ela_std_authentic"] = float(optimal_threshold * 0.3)

                print(f"  ✓ Optimal ELA std threshold: {optimal_threshold:.2f}")

        return threshold_analysis

    def generate_report(
        self,
        metrics: Dict[str, float],
        confidence_intervals: Dict[str, Tuple[float, float, float]],
        threshold_analysis: Dict,
        output_path: Path
    ):
        """Generate validation report."""
        print(f"\n📝 Generating validation report...")

        report = {
            "validation_summary": {
                "dataset": str(self.dataset_path),
                "bootstrap_iterations": self.bootstrap_iterations,
                "prediction_mode": self.prediction_mode,
                "medgemma_enabled": self.use_medgemma,
                "medgemma_stats": self.medgemma_stats if self.use_medgemma else None,
                "timestamp": pd.Timestamp.now().isoformat()
            },
            "metrics": metrics,
            "confidence_intervals_95": {
                metric: {
                    "mean": mean,
                    "lower_ci": lower,
                    "upper_ci": upper,
                    "ci_width": upper - lower
                }
                for metric, (mean, lower, upper) in confidence_intervals.items()
            },
            "threshold_analysis": threshold_analysis
        }

        # Save JSON report
        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"  ✓ Report saved to {output_path}")

        # Print summary
        print("\n" + "=" * 60)
        print("VALIDATION RESULTS SUMMARY")
        print("=" * 60)

        print("\n📊 Performance Metrics with 95% Confidence Intervals:")
        for metric, (mean, lower, upper) in confidence_intervals.items():
            print(f"  {metric.upper():12s}: {mean:.3f} [{lower:.3f}, {upper:.3f}]")

        print("\n🎯 ELA Threshold Analysis:")
        print(f"  Authentic images - ELA std mean: {threshold_analysis['authentic_ela_std']['mean']:.2f}")
        print(f"  Manipulated images - ELA std mean: {threshold_analysis['manipulated_ela_std']['mean']:.2f}")

        if threshold_analysis["recommended_thresholds"]:
            print("\n💡 Recommended Threshold Updates:")
            for key, value in threshold_analysis["recommended_thresholds"].items():
                print(f"  {key}: {value:.2f}")

        print("\n" + "=" * 60)

    def run_validation(self, output_dir: Path):
        """Run complete validation pipeline."""
        print("=" * 60)
        print("MedContext Forensics Validation")
        print("=" * 60)

        # Load dataset
        images, ground_truth = self.load_dataset()

        # Run predictions
        predictions = self.run_predictions(images)

        # Print prediction distribution for selected mode
        from collections import Counter
        verdicts = []
        for pred in predictions:
            if self.prediction_mode == "layer_1":
                verdicts.append(pred.layer_1.verdict)
            elif self.prediction_mode == "layer_2":
                verdicts.append(pred.layer_2.verdict)
            elif self.prediction_mode == "layer_3":
                verdicts.append(pred.layer_3.verdict)
            else:
                verdicts.append(pred.final_verdict)
        print(f"\n🧪 Prediction mode: {self.prediction_mode}")
        print(f"🧠 MedGemma enabled: {self.use_medgemma}")
        if self.use_medgemma:
            calls = self.medgemma_stats["calls"]
            errors = self.medgemma_stats["errors"]
            uncertain = self.medgemma_stats["uncertain"]
            print(
                f"🧠 MedGemma stats: calls={calls}, uncertain={uncertain}, errors={errors}"
            )
            if self.medgemma_stats["error_samples"]:
                print("🧠 MedGemma error samples:")
                for sample in self.medgemma_stats["error_samples"]:
                    print(f"  - {sample}")
        print(f"🧮 Verdict distribution: {Counter(verdicts)}")

        # Compute metrics
        metrics = self.compute_metrics(ground_truth, predictions)

        # Bootstrap confidence intervals
        confidence_intervals = self.bootstrap_confidence_intervals(
            ground_truth, predictions
        )

        # Analyze thresholds
        threshold_analysis = self.analyze_layer_thresholds(images, ground_truth)

        # Generate report
        output_dir.mkdir(parents=True, exist_ok=True)
        report_path = output_dir / "forensics_validation_report.json"
        self.generate_report(metrics, confidence_intervals, threshold_analysis, report_path)

        return report_path


def main():
    parser = argparse.ArgumentParser(description="Validate forensics detection with confidence intervals")
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to validation dataset directory"
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap iterations (default: 1000)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="validation_results",
        help="Output directory for reports (default: validation_results)"
    )
    parser.add_argument(
        "--balance",
        action="store_true",
        help="Balance classes by undersampling to minority count"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for balancing (default: 42)"
    )
    parser.add_argument(
        "--prediction-mode",
        type=str,
        default="ensemble",
        choices=["ensemble", "layer_1", "layer_2", "layer_3"],
        help="Which prediction to score (default: ensemble)"
    )
    parser.add_argument(
        "--use-medgemma",
        action="store_true",
        help="Use MedGemma for layer_2 predictions"
    )
    parser.add_argument(
        "--medgemma-prompt",
        type=str,
        default=None,
        help="Custom prompt for MedGemma (JSON with verdict/confidence)"
    )

    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    if not dataset_path.exists():
        print(f"❌ Dataset not found: {dataset_path}")
        print("\nExpected structure:")
        print("  dataset/")
        print("    authentic/")
        print("      image1.jpg")
        print("    manipulated/")
        print("      fake1.jpg")
        sys.exit(1)

    output_dir = Path(args.output)

    validator = ForensicsValidator(
        dataset_path,
        args.bootstrap,
        balance=args.balance,
        seed=args.seed,
        prediction_mode=args.prediction_mode,
        use_medgemma=args.use_medgemma,
        medgemma_prompt=args.medgemma_prompt,
    )
    report_path = validator.run_validation(output_dir)

    print(f"\n✅ Validation complete! Report: {report_path}")


if __name__ == "__main__":
    main()
