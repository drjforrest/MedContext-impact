#!/usr/bin/env python3
"""
Context Signal Validation Script - Compute Confidence Intervals

This script validates legacy image integrity signals against
public medical imaging datasets and computes statistical confidence intervals.

Datasets Supported:
1. MedFake: Medical Image Tamper Dataset (Kaggle)
2. FakeMed: Synthetic Medical Image Validation Challenge
3. Custom dataset (place in data/validation/)

Usage:
    python scripts/validate_forensics.py --dataset medifake --bootstrap 1000

Requirements:
    pip install scipy scikit-learn pandas seaborn matplotlib
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple
import io

import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
import pandas as pd

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app.clinical.medgemma_client import (
    MedGemmaClient,
    MedGemmaClientError,
    MedGemmaResult,
)

FORENSICS_SOURCE = "scripts.validate_forensics"

try:
    from PIL import Image, ImageChops, ExifTags
except ImportError:
    Image = None
    ImageChops = None
    ExifTags = None


@dataclass(frozen=True)
class IntegrityLayerResult:
    verdict: str
    confidence: float
    details: dict[str, Any]


@dataclass(frozen=True)
class IntegrityEnsembleResult:
    final_verdict: str
    confidence: float
    layer_1: IntegrityLayerResult
    layer_2: IntegrityLayerResult
    layer_3: IntegrityLayerResult


def run_layer_1(image_bytes: bytes) -> IntegrityLayerResult:
    """Fallback Layer 1: basic error level analysis."""
    if Image is None or ImageChops is None:
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": "PIL not available", "method": "error_level_analysis"},
        )

    try:
        original = Image.open(io.BytesIO(image_bytes))
        if original.mode not in ("RGB", "L"):
            original = original.convert("RGB")

        temp_buffer = io.BytesIO()
        original.save(temp_buffer, format="JPEG", quality=95)
        temp_buffer.seek(0)
        compressed = Image.open(temp_buffer)

        ela_image = ImageChops.difference(original, compressed)
        # Normalize ELA to amplify the error-level signal and keep scale consistent.
        ela_gray = ela_image.convert("L")
        ela_array = np.array(ela_gray, dtype=np.float32)
        ela_max_raw = float(np.max(ela_array)) if ela_array.size else 0.0
        if ela_max_raw > 0:
            ela_array = ela_array * (255.0 / ela_max_raw)

        ela_mean = float(np.mean(ela_array))
        ela_std = float(np.std(ela_array))
        ela_max = float(np.max(ela_array)) if ela_array.size else 0.0

        verdict = "UNCERTAIN"
        confidence = 0.5
        if ela_std > 0.74 and ela_max > 100:
            verdict = "MANIPULATED"
            confidence = min(0.85, 0.5 + (ela_std / 50.0))
        elif ela_std < 0.22 and ela_max < 50:
            verdict = "AUTHENTIC"
            confidence = min(0.80, 0.5 + (1.0 - ela_std / 10.0))

        return IntegrityLayerResult(
            verdict=verdict,
            confidence=confidence,
            details={
                "method": "error_level_analysis",
                "ela_mean": round(ela_mean, 2),
                "ela_std": round(ela_std, 2),
                "ela_max": round(ela_max, 2),
                "ela_max_raw": round(ela_max_raw, 2),
                "image_size": original.size,
                "image_mode": original.mode,
            },
        )
    except Exception as exc:
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": str(exc), "method": "error_level_analysis"},
        )


def run_layer_2(image_bytes: bytes) -> IntegrityLayerResult:
    del image_bytes
    return IntegrityLayerResult(
        verdict="UNCERTAIN",
        confidence=0.5,
        details={
            "method": "semantic_analysis",
            "note": "MedGemma disabled in fallback mode",
        },
    )


def run_layer_3(image_bytes: bytes) -> IntegrityLayerResult:
    """Fallback Layer 3: minimal EXIF checks."""
    if Image is None:
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": "PIL not available", "method": "exif_analysis"},
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))
        exif_data = image.getexif()

        if not exif_data:
            return IntegrityLayerResult(
                verdict="UNCERTAIN",
                confidence=0.25,
                details={
                    "method": "exif_analysis",
                    "warning": "Missing EXIF metadata",
                    "has_exif": False,
                },
            )

        exif_dict: dict[str, Any] = {}
        software_tags: list[str] = []
        suspicious_patterns: list[str] = []

        for tag_id, value in exif_data.items():
            tag_name = None
            if ExifTags is not None:
                tag_name = ExifTags.TAGS.get(tag_id)
            tag_name = tag_name or str(tag_id)
            exif_dict[tag_name] = str(value)

            if tag_name in ("Software", "ProcessingSoftware", "HostComputer"):
                software_tags.append(str(value).lower())
                editing_tools = [
                    "photoshop",
                    "gimp",
                    "paint.net",
                    "affinity",
                    "pixelmator",
                    "canva",
                ]
                for tool in editing_tools:
                    if tool in str(value).lower():
                        suspicious_patterns.append(
                            f"Editing software detected: {value}"
                        )

        ai_signatures = ["midjourney", "stable diffusion", "dall-e", "dalle", "ai"]
        ai_signature_patterns = {
            sig: re.compile(rf"\b{re.escape(sig)}\b") for sig in ai_signatures
        }
        for key, value in exif_dict.items():
            value_lower = str(value).lower()
            for sig, pattern in ai_signature_patterns.items():
                if pattern.search(value_lower):
                    suspicious_patterns.append(f"AI signature in {key}: {value}")

        verdict = "UNCERTAIN"
        confidence = 0.5
        if suspicious_patterns:
            verdict = "MANIPULATED"
            confidence = min(0.90, 0.6 + len(suspicious_patterns) * 0.15)
        elif software_tags:
            verdict = "AUTHENTIC"
            confidence = 0.70
        elif len(exif_dict) > 10:
            verdict = "AUTHENTIC"
            confidence = 0.75

        return IntegrityLayerResult(
            verdict=verdict,
            confidence=confidence,
            details={
                "method": "exif_analysis",
                "has_exif": True,
                "exif_fields_count": len(exif_dict),
                "suspicious_patterns": suspicious_patterns,
                "software_tags": software_tags,
                "key_fields": {
                    k: v
                    for k, v in exif_dict.items()
                    if k
                    in ("Make", "Model", "Software", "DateTime", "DateTimeOriginal")
                },
            },
        )
    except Exception as exc:
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": str(exc), "method": "exif_analysis"},
        )


def run_integrity_checks(image_bytes: bytes) -> IntegrityEnsembleResult:
    layer_1 = run_layer_1(image_bytes)
    layer_2 = run_layer_2(image_bytes)
    layer_3 = run_layer_3(image_bytes)

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
            confidence = (
                0.90 if authentic_votes == 3 else 0.75 if authentic_votes == 2 else 0.60
            )
        elif manipulated_votes > authentic_votes:
            final_verdict = "MANIPULATED"
            confidence = (
                0.90
                if manipulated_votes == 3
                else 0.75 if manipulated_votes == 2 else 0.60
            )
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

    return IntegrityEnsembleResult(
        final_verdict=final_verdict,
        confidence=round(confidence, 2),
        layer_1=layer_1,
        layer_2=layer_2,
        layer_3=layer_3,
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
        if (self.dataset_path / "real").exists() and (
            self.dataset_path / "fake"
        ).exists():
            images, labels = self._load_medforensics_format()
        elif (self.dataset_path / "original").exists() and (
            self.dataset_path / "tampered"
        ).exists():
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
            for img_path in list(authentic_dir.glob("*.jpg")) + list(
                authentic_dir.glob("*.png")
            ):
                with open(img_path, "rb") as f:
                    images.append(f.read())
                    labels.append("AUTHENTIC")
            print(
                "  ✓ Loaded "
                f"{sum(1 for label in labels if label == 'AUTHENTIC')} authentic images"
            )

        # Load manipulated images
        manipulated_dir = self.dataset_path / "manipulated"
        if manipulated_dir.exists():
            for img_path in list(manipulated_dir.glob("*.jpg")) + list(
                manipulated_dir.glob("*.png")
            ):
                with open(img_path, "rb") as f:
                    images.append(f.read())
                    labels.append("MANIPULATED")
            print(
                "  ✓ Loaded "
                f"{sum(1 for label in labels if label == 'MANIPULATED')} manipulated images"
            )

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
                    for img_path in list(modality_dir.glob("*.jpg")) + list(
                        modality_dir.glob("*.png")
                    ):
                        with open(img_path, "rb") as f:
                            images.append(f.read())
                            labels.append("AUTHENTIC")
            print(
                "  ✓ Loaded "
                f"{sum(1 for label in labels if label == 'AUTHENTIC')} real images"
            )

        # Load fake images from all modality subdirs
        fake_dir = self.dataset_path / "fake"
        if fake_dir.exists():
            for modality_dir in fake_dir.iterdir():
                if modality_dir.is_dir():
                    for img_path in list(modality_dir.glob("*.jpg")) + list(
                        modality_dir.glob("*.png")
                    ):
                        with open(img_path, "rb") as f:
                            images.append(f.read())
                            labels.append("MANIPULATED")
            print(
                "  ✓ Loaded "
                f"{sum(1 for label in labels if label == 'MANIPULATED')} fake images"
            )

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
            for img_path in list(original_dir.glob("*.jpg")) + list(
                original_dir.glob("*.png")
            ):
                with open(img_path, "rb") as f:
                    images.append(f.read())
                    labels.append("AUTHENTIC")
            print(
                "  ✓ Loaded "
                f"{sum(1 for label in labels if label == 'AUTHENTIC')} original images"
            )

        # Load tampered images
        tampered_dir = self.dataset_path / "tampered"
        if tampered_dir.exists():
            for img_path in list(tampered_dir.glob("*.jpg")) + list(
                tampered_dir.glob("*.png")
            ):
                with open(img_path, "rb") as f:
                    images.append(f.read())
                    labels.append("MANIPULATED")
            print(
                "  ✓ Loaded "
                f"{sum(1 for label in labels if label == 'MANIPULATED')} tampered images"
            )

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
                scan_id = (row.get("scan_id") or row.get("image_id") or "").strip()
                if scan_id:
                    scan_id = Path(scan_id).stem
                is_tampered = (
                    (row.get("is_tampered") or row.get("label") or "").strip().lower()
                )
                tampered_values = {"1", "true", "tampered", "yes", "y"}
                label_map[scan_id] = (
                    "MANIPULATED" if is_tampered in tampered_values else "AUTHENTIC"
                )

        # Load images
        images_dir = self.dataset_path / "images"
        if images_dir.exists():
            for img_path in list(images_dir.glob("*.jpg")) + list(
                images_dir.glob("*.png")
            ):
                scan_id = img_path.stem
                if scan_id in label_map:
                    with open(img_path, "rb") as f:
                        images.append(f.read())
                        labels.append(label_map[scan_id])

        print(f"  ✓ Loaded {len(images)} images with labels")
        print(f"    - Authentic: {sum(1 for label in labels if label == 'AUTHENTIC')}")
        print(
            "    - Manipulated: "
            f"{sum(1 for label in labels if label == 'MANIPULATED')}"
        )

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

    def run_predictions(self, images: List[bytes]) -> List[IntegrityEnsembleResult]:
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
                    result = run_integrity_checks(img_bytes)
                predictions.append(result)
            except Exception as e:
                print(f"  ⚠️  Error on image {idx}: {e}")
                # Create a fallback result
                fallback_layer = IntegrityLayerResult(
                    verdict="UNCERTAIN",
                    confidence=0.5,
                    details={"error": str(e), "source": "validation_fallback"},
                )
                predictions.append(
                    IntegrityEnsembleResult(
                        final_verdict="UNCERTAIN",
                        confidence=0.5,
                        layer_1=fallback_layer,
                        layer_2=fallback_layer,
                        layer_3=fallback_layer,
                    )
                )

        print(f"  ✓ Completed {len(predictions)} predictions")
        return predictions

    def _ensemble_from_layers(
        self,
        layer_1: IntegrityLayerResult,
        layer_2: IntegrityLayerResult,
        layer_3: IntegrityLayerResult,
    ) -> IntegrityEnsembleResult:
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

        return IntegrityEnsembleResult(
            final_verdict=final_verdict,
            confidence=round(confidence, 2),
            layer_1=layer_1,
            layer_2=layer_2,
            layer_3=layer_3,
        )

    def _run_medgemma_layer(self, image_bytes: bytes) -> IntegrityLayerResult:
        if self._medgemma_client is None:
            return IntegrityLayerResult(
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
            return IntegrityLayerResult(
                verdict="UNCERTAIN",
                confidence=0.5,
                details={"error": str(exc), "method": "medgemma"},
            )

        verdict, confidence, details = self._parse_medgemma_result(result)
        return IntegrityLayerResult(
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

    def _parse_medgemma_result(self, result: MedGemmaResult) -> tuple[str, float, dict]:
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
            text_candidate = str(
                parsed.get("text") or parsed.get("generated_text") or ""
            )
        if not text_candidate:
            text_candidate = raw_text
        if not text_candidate and output:
            text_candidate = str(output)

        json_candidate = None
        if isinstance(parsed, dict) and any(
            key in parsed for key in ("verdict", "confidence")
        ):
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
            if any(
                token in text_lower for token in ("manipulated", "tampered", "fake")
            ):
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
        self, ground_truth: List[str], predictions: List[IntegrityEnsembleResult]
    ) -> Dict[str, float]:
        """Compute classification metrics."""

        def select_prediction(pred: IntegrityEnsembleResult) -> tuple[str, float]:
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
                else (
                    0
                    if select_prediction(pred)[0] == "AUTHENTIC"
                    else (1 if select_prediction(pred)[1] > 0.5 else 0)
                )
            )
            for pred in predictions
        ]
        y_pred_scores = [select_prediction(pred)[1] for pred in predictions]

        return {
            "accuracy": accuracy_score(y_true, y_pred_labels),
            "precision": precision_score(y_true, y_pred_labels, zero_division=0),
            "recall": recall_score(y_true, y_pred_labels, zero_division=0),
            "f1_score": f1_score(y_true, y_pred_labels, zero_division=0),
            "roc_auc": (
                roc_auc_score(y_true, y_pred_scores) if len(set(y_true)) > 1 else 0.5
            ),
        }

    def bootstrap_confidence_intervals(
        self,
        ground_truth: List[str],
        predictions: List[IntegrityEnsembleResult],
        alpha: float = 0.05,
    ) -> Dict[str, Tuple[float, float, float]]:
        """
        Compute bootstrap confidence intervals for metrics.

        Returns:
            Dict with metric_name: (mean, lower_ci, upper_ci)
        """
        print(
            f"\n📊 Computing bootstrap confidence intervals ({self.bootstrap_iterations} iterations)..."
        )

        n = len(ground_truth)
        bootstrap_metrics = {
            "accuracy": [],
            "precision": [],
            "recall": [],
            "f1_score": [],
            "roc_auc": [],
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
        self, images: List[bytes], ground_truth: List[str]
    ) -> Dict:
        """
        Analyze ELA thresholds to determine optimal values.

        Returns optimal thresholds based on ROC analysis.
        """
        print("\n🎯 Analyzing ELA thresholds...")

        ela_stats = {"authentic": [], "manipulated": []}
        ela_failures = 0

        invalid_labels = 0
        for img_bytes, label in zip(images, ground_truth):
            try:
                layer_1_result = run_layer_1(img_bytes)
                ela_metrics = {
                    "ela_mean": layer_1_result.details.get("ela_mean"),
                    "ela_std": layer_1_result.details.get("ela_std"),
                    "ela_max": layer_1_result.details.get("ela_max"),
                }

                if all(value is not None for value in ela_metrics.values()):
                    if label not in {"AUTHENTIC", "MANIPULATED"}:
                        invalid_labels += 1
                        continue
                    category = "authentic" if label == "AUTHENTIC" else "manipulated"
                    ela_stats[category].append(ela_metrics)
            except Exception:
                ela_failures += 1
                continue

        if not ela_stats["authentic"] or not ela_stats["manipulated"]:
            print("  ⚠️  ELA metrics missing for one or both classes.")
        if ela_failures:
            print(f"  ⚠️  ELA failed on {ela_failures} images.")
        if invalid_labels:
            print(f"  ⚠️  Skipped {invalid_labels} samples with invalid labels.")

        # Compute statistics
        threshold_analysis = {
            "authentic_ela_std": {
                "mean": (
                    np.mean([m["ela_std"] for m in ela_stats["authentic"]])
                    if ela_stats["authentic"]
                    else 0
                ),
                "median": (
                    np.median([m["ela_std"] for m in ela_stats["authentic"]])
                    if ela_stats["authentic"]
                    else 0
                ),
                "std": (
                    np.std([m["ela_std"] for m in ela_stats["authentic"]])
                    if ela_stats["authentic"]
                    else 0
                ),
            },
            "manipulated_ela_std": {
                "mean": (
                    np.mean([m["ela_std"] for m in ela_stats["manipulated"]])
                    if ela_stats["manipulated"]
                    else 0
                ),
                "median": (
                    np.median([m["ela_std"] for m in ela_stats["manipulated"]])
                    if ela_stats["manipulated"]
                    else 0
                ),
                "std": (
                    np.std([m["ela_std"] for m in ela_stats["manipulated"]])
                    if ela_stats["manipulated"]
                    else 0
                ),
            },
            "authentic_ela_max": {
                "mean": (
                    np.mean([m["ela_max"] for m in ela_stats["authentic"]])
                    if ela_stats["authentic"]
                    else 0
                ),
                "median": (
                    np.median([m["ela_max"] for m in ela_stats["authentic"]])
                    if ela_stats["authentic"]
                    else 0
                ),
                "std": (
                    np.std([m["ela_max"] for m in ela_stats["authentic"]])
                    if ela_stats["authentic"]
                    else 0
                ),
            },
            "manipulated_ela_max": {
                "mean": (
                    np.mean([m["ela_max"] for m in ela_stats["manipulated"]])
                    if ela_stats["manipulated"]
                    else 0
                ),
                "median": (
                    np.median([m["ela_max"] for m in ela_stats["manipulated"]])
                    if ela_stats["manipulated"]
                    else 0
                ),
                "std": (
                    np.std([m["ela_max"] for m in ela_stats["manipulated"]])
                    if ela_stats["manipulated"]
                    else 0
                ),
            },
            "recommended_thresholds": {},
        }

        # Derive thresholds from per-class distributions (percentiles / midpoint)
        if ela_stats["authentic"] and ela_stats["manipulated"]:
            authentic_vals = np.array(
                [m["ela_std"] for m in ela_stats["authentic"]], dtype=float
            )
            manipulated_vals = np.array(
                [m["ela_std"] for m in ela_stats["manipulated"]], dtype=float
            )
            authentic_max_vals = np.array(
                [m["ela_max"] for m in ela_stats["authentic"]], dtype=float
            )
            manipulated_max_vals = np.array(
                [m["ela_max"] for m in ela_stats["manipulated"]], dtype=float
            )

            authentic_p90 = float(np.percentile(authentic_vals, 90))
            manipulated_p10 = float(np.percentile(manipulated_vals, 10))
            mean_gap = float(np.mean(manipulated_vals) - np.mean(authentic_vals))
            overlap = manipulated_p10 <= authentic_p90

            threshold_analysis["separability"] = {
                "authentic_p90": authentic_p90,
                "manipulated_p10": manipulated_p10,
                "mean_gap": mean_gap,
                "overlap": overlap,
            }

            if overlap:
                midpoint = float(
                    (np.mean(authentic_vals) + np.mean(manipulated_vals)) / 2.0
                )
                threshold_analysis["recommended_thresholds"][
                    "ela_std_authentic"
                ] = midpoint
                threshold_analysis["recommended_thresholds"][
                    "ela_std_manipulated"
                ] = midpoint
                print(
                    f"  ⚠️  Overlapping ELA std distributions; using midpoint {midpoint:.2f}"
                )
            else:
                threshold_analysis["recommended_thresholds"][
                    "ela_std_authentic"
                ] = authentic_p90
                threshold_analysis["recommended_thresholds"][
                    "ela_std_manipulated"
                ] = manipulated_p10
                print(
                    "  ✓ Recommended ELA std thresholds "
                    f"(authentic_p90={authentic_p90:.2f}, manipulated_p10={manipulated_p10:.2f})"
                )

            # Always compute auxiliary thresholds using ELA max as a secondary signal.
            authentic_max_p90 = float(np.percentile(authentic_max_vals, 90))
            manipulated_max_p10 = float(np.percentile(manipulated_max_vals, 10))
            threshold_analysis["recommended_thresholds"][
                "ela_max_authentic"
            ] = authentic_max_p90
            threshold_analysis["recommended_thresholds"][
                "ela_max_manipulated"
            ] = manipulated_max_p10

        return threshold_analysis

    def generate_report(
        self,
        metrics: Dict[str, float],
        confidence_intervals: Dict[str, Tuple[float, float, float]],
        threshold_analysis: Dict,
        output_path: Path,
    ):
        """Generate validation report."""
        print("\n📝 Generating validation report...")

        report = {
            "validation_summary": {
                "dataset": str(self.dataset_path),
                "bootstrap_iterations": self.bootstrap_iterations,
                "prediction_mode": self.prediction_mode,
                "medgemma_enabled": self.use_medgemma,
                "forensics_source": FORENSICS_SOURCE,
                "medgemma_stats": self.medgemma_stats if self.use_medgemma else None,
                "timestamp": pd.Timestamp.now().isoformat(),
            },
            "metrics": metrics,
            "confidence_intervals_95": {
                metric: {
                    "mean": mean,
                    "lower_ci": lower,
                    "upper_ci": upper,
                    "ci_width": upper - lower,
                }
                for metric, (mean, lower, upper) in confidence_intervals.items()
            },
            "threshold_analysis": threshold_analysis,
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
        print(
            f"  Authentic images - ELA std mean: {threshold_analysis['authentic_ela_std']['mean']:.2f}"
        )
        print(
            f"  Manipulated images - ELA std mean: {threshold_analysis['manipulated_ela_std']['mean']:.2f}"
        )

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
        self.generate_report(
            metrics, confidence_intervals, threshold_analysis, report_path
        )

        return report_path


def main():
    parser = argparse.ArgumentParser(
        description="Validate forensics detection with confidence intervals"
    )
    parser.add_argument(
        "--dataset",
        type=str,
        required=True,
        help="Path to validation dataset directory",
    )
    parser.add_argument(
        "--bootstrap",
        type=int,
        default=1000,
        help="Number of bootstrap iterations (default: 1000)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="validation_results",
        help="Output directory for reports (default: validation_results)",
    )
    parser.add_argument(
        "--balance",
        action="store_true",
        help="Balance classes by undersampling to minority count",
    )
    parser.add_argument(
        "--seed", type=int, default=42, help="Random seed for balancing (default: 42)"
    )
    parser.add_argument(
        "--prediction-mode",
        type=str,
        default="ensemble",
        choices=["ensemble", "layer_1", "layer_2", "layer_3"],
        help="Which prediction to score (default: ensemble)",
    )
    parser.add_argument(
        "--use-medgemma",
        action="store_true",
        help="Use MedGemma for layer_2 predictions",
    )
    parser.add_argument(
        "--medgemma-prompt",
        type=str,
        default=None,
        help="Custom prompt for MedGemma (JSON with verdict/confidence)",
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
