from __future__ import annotations

import io
import json
from dataclasses import dataclass
from uuid import uuid4

import numpy as np
from PIL import ExifTags, Image, ImageChops

from app.clinical.medgemma_client import MedGemmaClient, MedGemmaClientError
from app.core.config import settings


@dataclass(frozen=True)
class IntegrityLayerResult:
    verdict: str
    confidence: float
    details: dict[str, object]


@dataclass(frozen=True)
class Layer1Thresholds:
    ela_std_authentic: float
    ela_std_manipulated: float
    ela_max_authentic: float | None = None
    ela_max_manipulated: float | None = None


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


def _run_layer_1(
    image_bytes: bytes,
    thresholds: Layer1Thresholds | None = None,
) -> IntegrityLayerResult:
    try:
        original = Image.open(io.BytesIO(image_bytes))
        if original.mode not in ("RGB", "L"):
            original = original.convert("RGB")

        temp_buffer = io.BytesIO()
        original.save(temp_buffer, format="JPEG", quality=95)
        temp_buffer.seek(0)
        compressed = Image.open(temp_buffer)

        ela_image = ImageChops.difference(original, compressed)
        ela_gray = ela_image.convert("L")
        ela_array_raw = np.array(ela_gray, dtype=np.float32)
        ela_max_raw = float(np.max(ela_array_raw)) if ela_array_raw.size else 0.0
        ela_std_raw = float(np.std(ela_array_raw)) if ela_array_raw.size else 0.0
        ela_array = ela_array_raw.copy()
        scale = 1.0
        if ela_max_raw > 0:
            scale = 255.0 / ela_max_raw
            ela_array = ela_array * scale

        ela_mean = float(np.mean(ela_array))
        ela_std = float(np.std(ela_array))
        ela_max = float(np.max(ela_array)) if ela_array.size else 0.0

        verdict = "UNCERTAIN"
        confidence = 0.5
        if ela_array.size:
            if thresholds is None:
                thresholds = Layer1Thresholds(
                    ela_std_authentic=0.22,
                    ela_std_manipulated=0.74,
                )
            std_score = _normalize_score(
                ela_std, thresholds.ela_std_authentic, thresholds.ela_std_manipulated
            )
            if thresholds.ela_max_authentic is not None and (
                thresholds.ela_max_manipulated is not None
            ):
                max_score = _normalize_score(
                    ela_max,
                    thresholds.ela_max_authentic,
                    thresholds.ela_max_manipulated,
                )
                score = 0.8 * std_score + 0.2 * max_score
            else:
                score = std_score

            verdict = "MANIPULATED" if score >= 0.5 else "AUTHENTIC"
            confidence = max(score, 1.0 - score)

        return IntegrityLayerResult(
            verdict=verdict,
            confidence=confidence,
            details={
                "method": "error_level_analysis",
                "ela_mean": round(ela_mean, 2),
                "ela_std": round(ela_std, 2),
                "ela_max": round(ela_max, 2),
                "ela_max_raw": round(ela_max_raw, 2),
                "ela_std_raw": round(ela_std_raw, 4),
                "ela_scale": round(scale, 4),
                "image_size": original.size,
                "image_mode": original.mode,
                "thresholds": {
                    "ela_std_authentic": round(thresholds.ela_std_authentic, 4)
                    if thresholds
                    else None,
                    "ela_std_manipulated": round(thresholds.ela_std_manipulated, 4)
                    if thresholds
                    else None,
                    "ela_max_authentic": round(thresholds.ela_max_authentic, 4)
                    if thresholds and thresholds.ela_max_authentic is not None
                    else None,
                    "ela_max_manipulated": round(thresholds.ela_max_manipulated, 4)
                    if thresholds and thresholds.ela_max_manipulated is not None
                    else None,
                },
            },
        )
    except Exception as exc:
        return IntegrityLayerResult(
            verdict="UNCERTAIN",
            confidence=0.5,
            details={"error": str(exc), "method": "error_level_analysis"},
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

    verdict, confidence, details = _parse_medgemma_result(result.output, result.raw_text)
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
    if isinstance(parsed, dict) and any(key in parsed for key in ("verdict", "confidence")):
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
                    if k in ("Make", "Model", "Software", "DateTime", "DateTimeOriginal")
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
        "votes": {"AUTHENTIC": verdicts.count("AUTHENTIC"), "MANIPULATED": verdicts.count("MANIPULATED"), "UNCERTAIN": verdicts.count("UNCERTAIN")},
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
    selected_layers = [layer for layer in selected_layers if layer in {"layer_1", "layer_2", "layer_3"}]

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
