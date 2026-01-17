from __future__ import annotations

import re
from urllib.parse import urljoin

_META_IMAGE_RE = re.compile(
    r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_META_DESC_RE = re.compile(
    r'<meta[^>]+(?:name|property)=["\'](?:description|og:description)["\']'
    r'[^>]+content=["\']([^"\']+)["\']',
    re.IGNORECASE,
)
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
_IMG_SRC_RE = re.compile(
    r"<img[^>]+src=[\"']([^\"']+)[\"']", re.IGNORECASE
)


def extract_image_candidates(html: str, base_url: str) -> list[str]:
    if not html:
        return []
    candidates: list[str] = []
    for match in _META_IMAGE_RE.findall(html):
        _add_candidate(candidates, match, base_url)
    for match in _IMG_SRC_RE.findall(html):
        _add_candidate(candidates, match, base_url)
    return candidates


def extract_page_context(html: str, base_url: str) -> str | None:
    if not html:
        return None
    parts: list[str] = []
    title_match = _TITLE_RE.search(html)
    if title_match:
        title = _clean_text(title_match.group(1))
        if title:
            parts.append(title)
    for match in _META_DESC_RE.findall(html):
        description = _clean_text(match)
        if description:
            parts.append(description)
            break
    if not parts:
        return None
    return " — ".join(parts)


def _add_candidate(candidates: list[str], raw: str, base_url: str) -> None:
    cleaned = raw.strip()
    if not cleaned or cleaned.startswith("data:"):
        return
    resolved = urljoin(base_url, cleaned)
    if resolved not in candidates:
        candidates.append(resolved)


def _clean_text(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text or "").strip()
    return cleaned
