from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np

try:
    from PIL import Image, ImageChops, ImageFilter
except ImportError:
    Image = None
    ImageChops = None
    ImageFilter = None

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class DeepfakeLayerResult:
    verdict: str
    confidence: float
    details: dict[str, Any]


@dataclass(frozen=True)
class DeepfakeEnsembleResult:
    final_verdict: str
    confidence: float
    layer_1: DeepfakeLayerResult
    layer_2: DeepfakeLayerResult
    layer_3: DeepfakeLayerResult


def run_layer_1(image_bytes: bytes) -> DeepfakeLayerResult:
    """Layer 1: Pixel-level forensics using Error Level Analysis (ELA).

    ELA detects compression artifacts by re-saving the image at known quality
    and comparing differences. Manipulated regions show different error levels.
    """
    if Image is None:
        return DeepfakeLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": "PIL not available"},
        )

    try:
        # Load original image
        original = Image.open(io.BytesIO(image_bytes))
        if original.mode not in ("RGB", "L"):
            original = original.convert("RGB")

        # Re-save at quality 95 to generate error level
        temp_buffer = io.BytesIO()
        original.save(temp_buffer, format="JPEG", quality=95)
        temp_buffer.seek(0)
        compressed = Image.open(temp_buffer)

        # Calculate difference (Error Level Analysis)
        ela_image = ImageChops.difference(original, compressed)

        # Convert to numpy for analysis
        ela_array = np.array(ela_image)

        # Calculate statistics
        ela_mean = float(np.mean(ela_array))
        ela_std = float(np.std(ela_array))
        ela_max = float(np.max(ela_array))

        # Detection thresholds (tuned for medical images)
        # High variation in error levels suggests manipulation
        confidence = 0.5
        verdict = "UNCERTAIN"

        if ela_std > 0.74 and ela_max > 100:
            # High variation + high max error = likely manipulated
            verdict = "MANIPULATED"
            confidence = min(0.85, 0.5 + (ela_std / 50.0))
        elif ela_std < 0.22 and ela_max < 50:
            # Low variation + low max error = likely authentic
            verdict = "AUTHENTIC"
            confidence = min(0.80, 0.5 + (1.0 - ela_std / 10.0))

        return DeepfakeLayerResult(
            verdict=verdict,
            confidence=confidence,
            details={
                "method": "error_level_analysis",
                "ela_mean": round(ela_mean, 2),
                "ela_std": round(ela_std, 2),
                "ela_max": round(ela_max, 2),
                "image_size": original.size,
                "image_mode": original.mode,
            },
        )

    except Exception as exc:
        _LOGGER.warning("Layer 1 (ELA) analysis failed: %s", exc)
        return DeepfakeLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": str(exc), "method": "error_level_analysis"},
        )


def run_layer_2(image_bytes: bytes) -> DeepfakeLayerResult:
    """Layer 2: Semantic/content analysis.

    This layer is handled by MedGemma in the agent's triage step,
    so we return a placeholder that the agent can override with
    its plausibility assessment.
    """
    del image_bytes
    return DeepfakeLayerResult(
        verdict="UNCERTAIN",
        confidence=0.5,
        details={
            "method": "semantic_analysis",
            "note": "Delegated to MedGemma triage in agentic workflow",
        },
    )


def run_layer_3(image_bytes: bytes) -> DeepfakeLayerResult:
    """Layer 3: Metadata and provenance analysis via EXIF.

    Analyzes EXIF metadata for:
    - Missing or suspicious metadata patterns
    - Software signatures (image editing tools)
    - Timestamp inconsistencies
    - Camera/device information
    """
    if Image is None:
        return DeepfakeLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": "PIL not available"},
        )

    try:
        image = Image.open(io.BytesIO(image_bytes))
        exif_data = image.getexif()

        if not exif_data:
            # No EXIF data is suspicious for genuine medical imaging equipment
            return DeepfakeLayerResult(
                verdict="MANIPULATED",
                confidence=0.65,
                details={
                    "method": "exif_analysis",
                    "warning": "Missing EXIF metadata (suspicious for medical images)",
                    "has_exif": False,
                },
            )

        # Extract key EXIF fields
        exif_dict: dict[str, Any] = {}
        software_tags = []
        suspicious_patterns = []

        for tag_id, value in exif_data.items():
            try:
                tag_name = Image.ExifTags.TAGS.get(tag_id, str(tag_id))
                exif_dict[tag_name] = str(value)

                # Check for image editing software signatures
                if tag_name in ("Software", "ProcessingSoftware", "HostComputer"):
                    software_tags.append(str(value).lower())

                    # Known manipulation tools
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

            except Exception:
                continue

        # Check for AI generation signatures
        ai_signatures = ["midjourney", "stable diffusion", "dall-e", "dalle", "ai"]
        for key, value in exif_dict.items():
            value_lower = str(value).lower()
            for sig in ai_signatures:
                if sig in value_lower:
                    suspicious_patterns.append(f"AI signature in {key}: {value}")

        # Verdict based on findings
        confidence = 0.5
        verdict = "UNCERTAIN"

        if suspicious_patterns:
            verdict = "MANIPULATED"
            confidence = min(0.90, 0.6 + len(suspicious_patterns) * 0.15)
        elif software_tags and not suspicious_patterns:
            # Has software tags but not suspicious ones (medical imaging software)
            verdict = "AUTHENTIC"
            confidence = 0.70
        elif len(exif_dict) > 10:
            # Rich EXIF data without suspicious patterns
            verdict = "AUTHENTIC"
            confidence = 0.75

        return DeepfakeLayerResult(
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
                    in (
                        "Make",
                        "Model",
                        "Software",
                        "DateTime",
                        "DateTimeOriginal",
                    )
                },
            },
        )

    except Exception as exc:
        _LOGGER.warning("Layer 3 (EXIF) analysis failed: %s", exc)
        return DeepfakeLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": str(exc), "method": "exif_analysis"},
        )


def run_deepfake_layers(
    image_bytes: bytes, layers: list[str]
) -> dict[str, DeepfakeLayerResult]:
    results: dict[str, DeepfakeLayerResult] = {}
    for layer in layers:
        if layer == "layer_1":
            results[layer] = run_layer_1(image_bytes)
        elif layer == "layer_2":
            results[layer] = run_layer_2(image_bytes)
        elif layer == "layer_3":
            results[layer] = run_layer_3(image_bytes)
    return results


def run_deepfake_detection(image_bytes: bytes) -> DeepfakeEnsembleResult:
    """Multi-layer deepfake detection ensemble.

    Combines three analysis layers:
    - Layer 1: Pixel-level forensics (ELA)
    - Layer 2: Semantic analysis (MedGemma via agent)
    - Layer 3: Metadata analysis (EXIF)

    Ensemble decision logic:
    - All 3 agree: high confidence
    - 2 of 3 agree: medium confidence
    - 1 or 0 agree: low confidence + expert review
    """
    layer_1 = run_layer_1(image_bytes)
    layer_2 = run_layer_2(image_bytes)
    layer_3 = run_layer_3(image_bytes)

    # Count verdicts (excluding UNCERTAIN)
    verdicts = [layer_1.verdict, layer_2.verdict, layer_3.verdict]
    non_uncertain = [v for v in verdicts if v != "UNCERTAIN"]

    if not non_uncertain:
        # All layers uncertain
        final_verdict = "UNCERTAIN"
        confidence = 0.5
    else:
        # Count votes for each verdict
        authentic_votes = non_uncertain.count("AUTHENTIC")
        manipulated_votes = non_uncertain.count("MANIPULATED")

        if authentic_votes > manipulated_votes:
            final_verdict = "AUTHENTIC"
            # Confidence based on agreement
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
            # Tie
            final_verdict = "UNCERTAIN"
            confidence = 0.50

        # Weight by individual layer confidences
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
