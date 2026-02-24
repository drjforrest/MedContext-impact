from __future__ import annotations

import codecs
import io
import json
import logging
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)


def clean_llm_text(content: str) -> str:
    """Clean up common artifacts from LLM-generated text/JSON."""
    cleaned = content.strip()
    cleaned = cleaned.lstrip("|").strip()

    # Remove leading "JSON" markers that models sometimes add
    cleaned = re.sub(r"^JSON\s*\n+", "", cleaned, flags=re.IGNORECASE)

    # Remove <unused*> tags and thought markers
    cleaned = re.sub(r"<unused\d+>", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(
        r"^thought\s*:?\s*", "", cleaned, flags=re.IGNORECASE | re.MULTILINE
    )
    cleaned = re.sub(
        r"^tool_name\s*:.*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE
    )
    cleaned = re.sub(
        r"^tool_code\s*:.*$", "", cleaned, flags=re.IGNORECASE | re.MULTILINE
    )

    # Try to extract JSON from markdown code fences - this is critical
    json_fence = re.search(
        r"```json\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE
    )
    if json_fence:
        return json_fence.group(1).strip()

    # Try any code fence
    any_fence = re.search(r"```\s*(.*?)```", cleaned, flags=re.DOTALL)
    if any_fence:
        potential = any_fence.group(1).strip()
        # If it looks like JSON, use it
        if potential.startswith("{"):
            return potential

    # If content has reasoning before JSON, extract just the JSON part
    json_obj = extract_json_by_brackets(cleaned)
    if json_obj:
        return json_obj

    cleaned = re.sub(r"\s{3,}", "  ", cleaned)
    return cleaned.strip()


def extract_json_by_brackets(content: str) -> Optional[str]:
    """Extract JSON object using bracket counting for deeply nested structures."""
    start_idx = content.find("{")
    if start_idx == -1:
        return None

    depth = 0
    in_string = False
    escape_next = False
    end_idx = start_idx

    for i, char in enumerate(content[start_idx:], start=start_idx):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if in_string:
            continue

        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                end_idx = i
                break

    if depth == 0 and end_idx > start_idx:
        return content[start_idx : end_idx + 1]

    return None


def parse_llm_json(content: str) -> Any:
    """Robustly parse JSON from LLM output, handling common formatting issues."""

    def _try_load(raw: str) -> Any:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return None

    def _unescape_candidate(raw: str) -> str:
        try:
            return codecs.decode(raw, "unicode_escape")
        except (UnicodeDecodeError, ValueError):
            return raw

    # Try direct parsing first
    direct = _try_load(content)
    if direct is not None:
        return direct

    # Try to extract from markdown code fences (```json...```)
    fenced = re.search(r"```json\s*(.*?)```", content, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        candidate = fenced.group(1).strip()
        loaded = _try_load(candidate)
        if loaded is not None:
            return loaded
        unescaped = _unescape_candidate(candidate)
        loaded = _try_load(unescaped)
        if loaded is not None:
            return loaded

    # Try to extract from any code fence (```...```)
    fenced_any = re.search(r"```\s*(.*?)```", content, flags=re.DOTALL)
    if fenced_any:
        candidate = fenced_any.group(1).strip()
        loaded = _try_load(candidate)
        if loaded is not None:
            return loaded

    return None


def resize_image(image_bytes: bytes, max_size: int = 1024, quality: int = 80) -> bytes:
    """Resize image to fit within max_size pixels and re-encode as JPEG.

    Always returns the re-encoded image when dimensions were reduced, even if
    the file size increased — pixel dimensions matter more than byte count for
    CPU-based vision model inference.
    """
    try:
        from PIL import Image

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        was_resized = False
        if max(img.size) > max_size:
            ratio = max_size / max(img.size)
            new_size = tuple(int(dim * ratio) for dim in img.size)
            img = img.resize(new_size, Image.Resampling.LANCZOS)
            was_resized = True

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=quality)
        resized = buffer.getvalue()

        # Always return the JPEG re-encoded version. Even when dimensions
        # weren't reduced, the original might be a format (palette PNG,
        # WebP, etc.) that downstream vision APIs can't handle.
        return resized
    except Exception as e:
        logger.warning(f"Image resize failed: {e}")
        return image_bytes


def detect_image_format(image_bytes: bytes) -> str:
    """Detect image format using PIL."""
    try:
        from PIL import Image

        with Image.open(io.BytesIO(image_bytes)) as image:
            image_format = (image.format or "JPEG").lower()
    except Exception:
        image_format = "jpeg"
    if image_format == "jpg":
        image_format = "jpeg"
    return image_format


def looks_like_reasoning(text: str) -> bool:
    """Check if text looks like model reasoning/thinking rather than a final output."""
    if not text or len(text) < 50:
        return False
    text_lower = text.lower()
    reasoning_indicators = [
        "the user wants me to",
        "i need to generate",
        "constraint checklist",
        "confidence score:",
        "mental sandbox",
        "let me analyze",
        "i will now",
        "step 1:",
        "first, i need to",
        "my task is to",
        "i should respond",
        "**constraint",
        "**checklist",
    ]
    indicator_count = sum(1 for ind in reasoning_indicators if ind in text_lower)
    if indicator_count >= 2:
        return True
    # Long text with multiple asterisks (markdown formatting in reasoning)
    if len(text) > 500 and text.count("**") > 4:
        return True
    return False
