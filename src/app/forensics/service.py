from __future__ import annotations

import io
import json
from dataclasses import dataclass
from uuid import uuid4

import numpy as np
from PIL import ExifTags, Image

from app.clinical.medgemma_client import MedGemmaClient, MedGemmaClientError
from app.core.config import settings


@dataclass(frozen=True)
class IntegrityLayerResult:
    verdict: str
    confidence: float
    details: dict[str, object]


_DICOM_MAGIC_OFFSET = 128
_DICOM_MAGIC = b"DICM"
_COPY_MOVE_SUSPECT_THRESHOLD = 0.02


DEFAULT_MEDGEMMA_PROMPT = (
    "You are a medical image forensics assistant. "
    "Assess whether the image is authentic or manipulated. "
    "Return JSON with keys: verdict (AUTHENTIC|MANIPULATED|UNCERTAIN), "
    "confidence (0-1), rationale."
)


def _normalize_score(value: float, low: float, high: float) -> float:
    if high <= low:
        return 0.5
    return max(0.0, min(1.0, (value - low) / (high - low)))


def _is_dicom(image_bytes: bytes) -> bool:
    return (
        len(image_bytes) > _DICOM_MAGIC_OFFSET + 4
        and image_bytes[_DICOM_MAGIC_OFFSET : _DICOM_MAGIC_OFFSET + 4] == _DICOM_MAGIC
    )


def _copy_move_score(
    slice_img: np.ndarray,
    patch_size: int = 16,
    stride: int = 8,
    similarity_threshold: float = 0.98,
    max_pairs: int = 5000,
) -> float:
    """Heuristic copy-move score on a normalized 2D float32 slice.

    Samples random non-overlapping patch pairs and counts those with cosine
    similarity above *similarity_threshold*.  A score >_COPY_MOVE_SUSPECT_THRESHOLD
    is treated as suspicious.  This is a placeholder heuristic; swap for a
    trained CNN without touching any calling code.
    """
    h, w = slice_img.shape
    patches: list[np.ndarray] = []
    coords: list[tuple[int, int]] = []

    for y in range(0, h - patch_size + 1, stride):
        for x in range(0, w - patch_size + 1, stride):
            patches.append(
                slice_img[y : y + patch_size, x : x + patch_size].reshape(-1)
            )
            coords.append((y, x))

    n = len(patches)
    if n < 2:
        return 0.0

    patches_arr = np.stack(patches, axis=0)
    norms = np.linalg.norm(patches_arr, axis=1, keepdims=True) + 1e-8
    patches_norm = patches_arr / norms

    rng = np.random.default_rng(42)
    # Over-sample candidates to reach max_pairs valid (non-adjacent) pairs
    candidates = rng.integers(0, n, size=(max_pairs * 4, 2))

    suspicious = 0
    total = 0
    for pair in candidates:
        i, j = int(pair[0]), int(pair[1])
        if i == j:
            continue
        y1, x1 = coords[i]
        y2, x2 = coords[j]
        if abs(y1 - y2) < patch_size and abs(x1 - x2) < patch_size:
            continue
        if float(np.dot(patches_norm[i], patches_norm[j])) >= similarity_threshold:
            suspicious += 1
        total += 1
        if total >= max_pairs:
            break

    return suspicious / total if total > 0 else 0.0


def _run_layer_1_dicom(image_bytes: bytes) -> IntegrityLayerResult:
    """DICOM-native pixel forensics replacing ELA for medical images.

    Performs two complementary checks:
    1. Header integrity  – verifies required DICOM UIDs and geometry tags.
    2. Copy-move score   – detects cloned regions directly on the native
                           float32 pixel array (no JPEG round-trip).
    """
    try:
        import pydicom

        ds = pydicom.dcmread(io.BytesIO(image_bytes))

        # --- 1. Header integrity ---
        issues: list[str] = []
        for tag in ("StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID"):
            if not getattr(ds, tag, None):
                issues.append(f"missing_{tag.lower()}")

        rows = getattr(ds, "Rows", None)
        cols = getattr(ds, "Columns", None)
        if not rows or not cols:
            issues.append("missing_dimensions")

        px_spacing = getattr(ds, "PixelSpacing", None)
        if px_spacing is not None and len(px_spacing) != 2:
            issues.append("invalid_pixel_spacing")

        sl_thick = getattr(ds, "SliceThickness", None)
        if sl_thick is not None and float(sl_thick) <= 0:
            issues.append("invalid_slice_thickness")

        acq_date = getattr(ds, "AcquisitionDate", None)
        acq_time = getattr(ds, "AcquisitionTime", None)
        if bool(acq_date) != bool(acq_time):
            issues.append("partial_acquisition_timestamp")

        header_ok = len(issues) == 0

        # --- 2. Pixel copy-move analysis ---
        pixels = ds.pixel_array.astype(np.float32)
        pixel_shape = list(pixels.shape)

        if pixels.ndim == 3:
            # Could be (frames, rows, cols) or (rows, cols, channels)
            if pixels.shape[2] <= 4:  # Likely RGB/RGBA
                slice_img: np.ndarray = pixels[:, :, 0]  # Take first channel
            else:
                slice_img = pixels[pixels.shape[0] // 2]
        elif pixels.ndim == 2:
            slice_img = pixels
        elif pixels.ndim == 4:
            # Multi-frame with channels: (frames, rows, cols, channels)
            slice_img = pixels[pixels.shape[0] // 2, :, :, 0]
        else:
            issues.append(f"unsupported_pixel_dims_{pixels.ndim}")
            slice_img = np.zeros((1, 1), dtype=np.float32)

        pmin, pmax = (
            float(np.percentile(slice_img, 1)),
            float(np.percentile(slice_img, 99)),
        )
        if pmax > pmin:
            slice_norm = np.clip((slice_img - pmin) / (pmax - pmin), 0.0, 1.0)
        else:
            slice_norm = np.zeros_like(slice_img)

        copy_move_score = _copy_move_score(slice_norm)

        # --- 3. Verdict ---
        if not header_ok:
            verdict = "MANIPULATED"
            confidence = 0.70
        elif copy_move_score > _COPY_MOVE_SUSPECT_THRESHOLD:
            verdict = "MANIPULATED"
            confidence = min(0.85, 0.60 + copy_move_score * 10.0)
        else:
            verdict = "AUTHENTIC"
            confidence = max(0.60, 0.85 - copy_move_score * 10.0)

        return IntegrityLayerResult(
            verdict=verdict,
            confidence=confidence,
            details={
                "method": "dicom_native_forensics",
                "header_ok": header_ok,
                "header_issues": issues,
                "copy_move_score": round(copy_move_score, 4),
                "pixel_shape": pixel_shape,
                "modality": getattr(ds, "Modality", None),
                "rows": rows,
                "columns": cols,
            },
        )
    except Exception:
        import logging

        logging.exception("DICOM forensics layer_1 failed")
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={
                "error": "DICOM analysis failed",
                "method": "dicom_native_forensics",
            },
        )


def _run_layer_1(image_bytes: bytes) -> IntegrityLayerResult:
    if _is_dicom(image_bytes):
        return _run_layer_1_dicom(image_bytes)
    try:
        image = Image.open(io.BytesIO(image_bytes))
        if image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        gray = image.convert("L")
        pixel_array = np.array(gray, dtype=np.float32)

        pmin = float(np.percentile(pixel_array, 1))
        pmax = float(np.percentile(pixel_array, 99))
        if pmax > pmin:
            pixel_norm = np.clip((pixel_array - pmin) / (pmax - pmin), 0.0, 1.0)
        else:
            pixel_norm = np.zeros_like(pixel_array)

        copy_move_score = _copy_move_score(pixel_norm)

        if copy_move_score > _COPY_MOVE_SUSPECT_THRESHOLD:
            verdict = "MANIPULATED"
            confidence = min(0.85, 0.60 + copy_move_score * 10.0)
        else:
            verdict = "AUTHENTIC"
            confidence = max(0.60, 0.85 - copy_move_score * 10.0)

        return IntegrityLayerResult(
            verdict=verdict,
            confidence=confidence,
            details={
                "method": "pixel_forensics",
                "copy_move_score": round(copy_move_score, 4),
                "image_size": list(image.size),
                "image_mode": image.mode,
            },
        )
    except Exception as exc:
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": str(exc), "method": "pixel_forensics"},
        )


def _run_layer_2(image_bytes: bytes) -> IntegrityLayerResult:
    if not settings.enable_forensics_medgemma:
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={
                "method": "semantic_analysis",
                "note": "MedGemma disabled for forensics layer_2",
            },
        )
    try:
        client = MedGemmaClient()
        result = client.analyze_image(
            image_bytes=image_bytes, prompt=DEFAULT_MEDGEMMA_PROMPT
        )
    except MedGemmaClientError as exc:
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": str(exc), "method": "semantic_analysis"},
        )

    verdict, confidence, details = _parse_medgemma_result(
        result.output, result.raw_text
    )
    return IntegrityLayerResult(
        verdict=verdict,
        confidence=confidence,
        details={
            "method": "semantic_analysis",
            "parsed": details,
        },
    )


def _parse_medgemma_result(
    output: object, raw_text: str | None
) -> tuple[str, float, dict[str, object]]:
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
        text_candidate = raw_text or ""
    if not text_candidate and output:
        text_candidate = str(output)

    json_candidate = None
    if isinstance(parsed, dict) and any(
        key in parsed for key in ("verdict", "confidence")
    ):
        json_candidate = parsed
    else:
        try:
            match = json.loads(text_candidate)
        except (json.JSONDecodeError, TypeError):
            match = None
        if isinstance(match, dict):
            json_candidate = match

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


def _run_layer_3(image_bytes: bytes) -> IntegrityLayerResult:
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

        exif_dict: dict[str, object] = {}
        software_tags: list[str] = []
        suspicious_patterns: list[str] = []

        for tag_id, value in exif_data.items():
            tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
            exif_dict[tag_name] = str(value)

            if tag_name in ("Software", "ProcessingSoftware", "HostComputer"):
                software_tags.append(str(value).lower())
                for tool in (
                    "photoshop",
                    "gimp",
                    "paint.net",
                    "affinity",
                    "pixelmator",
                    "canva",
                ):
                    if tool in str(value).lower():
                        suspicious_patterns.append(
                            f"Editing software detected: {value}"
                        )

        ai_signatures = (
            "midjourney",
            "stable diffusion",
            "dall-e",
            "dalle",
            "artificial intelligence",
            "generated by ai",
            "ai-generated",
            "ai generated",
        )
        for key, value in exif_dict.items():
            value_lower = str(value).lower()
            for sig in ai_signatures:
                if sig in value_lower:
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


def _ensemble_results(results: list[IntegrityLayerResult]) -> dict[str, object]:
    verdicts = [layer.verdict for layer in results]
    non_uncertain = [v for v in verdicts if v != "UNCERTAIN"]

    if not non_uncertain:
        final_verdict = "UNCERTAIN"
        confidence = 0.5
    else:
        authentic_votes = non_uncertain.count("AUTHENTIC")
        manipulated_votes = non_uncertain.count("MANIPULATED")

        if authentic_votes > manipulated_votes:
            final_verdict = "AUTHENTIC"
            confidence = 0.75 if authentic_votes >= 2 else 0.60
        elif manipulated_votes > authentic_votes:
            final_verdict = "MANIPULATED"
            confidence = 0.75 if manipulated_votes >= 2 else 0.60
        else:
            final_verdict = "UNCERTAIN"
            confidence = 0.50

        matching = [layer for layer in results if layer.verdict == final_verdict]
        if matching:
            avg_confidence = sum(layer.confidence for layer in matching) / len(matching)
            confidence = min(confidence, avg_confidence * 1.1)

    return {
        "final_verdict": final_verdict,
        "confidence": round(float(confidence), 2),
        "votes": {
            "AUTHENTIC": verdicts.count("AUTHENTIC"),
            "MANIPULATED": verdicts.count("MANIPULATED"),
            "UNCERTAIN": verdicts.count("UNCERTAIN"),
        },
    }


def run_forensics(image_bytes: bytes, layers: list[str] | None = None) -> dict:
    response: dict[str, object] = {
        "job_id": uuid4(),
    }
    if not settings.enable_forensics:
        response.update(
            {
                "status": "skipped",
                "detail": "forensics disabled by configuration",
                "selected_layers": list(layers) if layers else [],
            }
        )
        return response

    requested = [layer.strip().lower() for layer in (layers or []) if layer]
    selected_layers = requested or ["layer_1", "layer_2", "layer_3"]
    selected_layers = [
        layer for layer in selected_layers if layer in {"layer_1", "layer_2", "layer_3"}
    ]

    results: dict[str, IntegrityLayerResult] = {}
    if "layer_1" in selected_layers:
        results["layer_1"] = _run_layer_1(image_bytes)
    if "layer_2" in selected_layers:
        results["layer_2"] = _run_layer_2(image_bytes)
    if "layer_3" in selected_layers:
        results["layer_3"] = _run_layer_3(image_bytes)

    response.update(
        {
            "status": "completed",
            "detail": "forensics completed",
            "selected_layers": selected_layers,
            "layers": {
                key: {
                    "verdict": value.verdict,
                    "confidence": round(float(value.confidence), 4),
                    "details": value.details,
                }
                for key, value in results.items()
            },
            "ensemble": _ensemble_results(list(results.values())),
        }
    )
    return response
