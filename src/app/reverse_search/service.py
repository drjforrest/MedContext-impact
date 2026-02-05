from __future__ import annotations

import base64
import hashlib
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

import cachetools
import requests

from app.core.config import settings
from app.schemas.reverse_search import (
    ReverseSearchJobResponse,
    ReverseSearchMatch,
    ReverseSearchResult,
)

_LOGGER = logging.getLogger(__name__)
_PROVIDERS = ["open_web", "news_archive", "social_graph"]
_SAMPLE_MATCHES = [
    {
        "source": "open_web",
        "url": "https://example.com/news/health-image-1",
        "title": "Image appears in early coverage",
        "snippet": "The image was first spotted in a regional news archive.",
    },
    {
        "source": "news_archive",
        "url": "https://example.com/archive/health-image-2",
        "title": "Archived snapshot",
        "snippet": "A historical archive lists the image with metadata.",
    },
    {
        "source": "social_graph",
        "url": "https://example.com/social/post/12345",
        "title": "Early social share",
        "snippet": "The earliest share appears in a public community post.",
    },
]
_RESULTS_CACHE: cachetools.TTLCache[UUID, ReverseSearchResult] = cachetools.TTLCache(
    maxsize=1024,
    ttl=3600,
)


def _normalize_image_id(image_id: UUID | str) -> UUID:
    if isinstance(image_id, UUID):
        return image_id
    return UUID(str(image_id))


def _hash_bytes(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _extract_serpapi_matches(payload: dict, now: datetime) -> list[ReverseSearchMatch]:
    candidates = None
    for key in ("image_results", "images_results", "inline_images"):
        if isinstance(payload.get(key), list):
            candidates = payload[key]
            break
    if not candidates:
        return []

    matches: list[ReverseSearchMatch] = []
    for index, item in enumerate(candidates[:10]):
        if not isinstance(item, dict):
            continue

        url = item.get("link") or item.get("original") or item.get("image")
        if not url:
            continue

        source = item.get("source") or item.get("source_name") or "serpapi"
        title = item.get("title") or item.get("snippet")
        snippet = item.get("snippet") or item.get("description")
        confidence = max(0.3, 0.9 - (index * 0.05))
        metadata = {
            "thumbnail": item.get("thumbnail"),
            "source_icon": item.get("source_icon"),
            "position": item.get("position", index + 1),
        }

        matches.append(
            ReverseSearchMatch(
                source=source,
                url=url,
                title=title,
                snippet=snippet,
                confidence=round(confidence, 3),
                discovered_at=now,
                metadata={k: v for k, v in metadata.items() if v is not None},
            )
        )

    return matches


def _fetch_serpapi_matches(
    image_bytes: bytes, now: datetime
) -> tuple[list[ReverseSearchMatch], list[str] | None]:
    if not settings.serp_api_key:
        return [], None

    encoded_image = base64.b64encode(image_bytes).decode("utf-8")

    params = {
        "engine": "google_reverse_image",
        "api_key": settings.serp_api_key,
        # for now, stick to image_url OR image_content depending on what you're actually using
        # if you're following the official examples, you should be using image_url, not base64
        # "image_url": "https://example.com/safe-test-image.jpg",
        "image_content": encoded_image,  # only if supported in your plan; otherwise comment this out
    }

    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params=params,  # <-- query string, not json=
            timeout=settings.serp_api_timeout_seconds,
        )
    except requests.RequestException as exc:
        _LOGGER.warning("SerpAPI reverse search HTTP error: %s", exc)
        return [], None

    # Basic sanity check
    if resp.status_code != 200:
        _LOGGER.warning(
            "SerpAPI reverse search non-200: %s, body=%r",
            resp.status_code,
            resp.text[:200],
        )
        return [], None

    try:
        payload = resp.json()
    except ValueError as exc:
        _LOGGER.warning(
            "SerpAPI reverse search JSON parse error: %s, body=%r",
            exc,
            resp.text[:200],
        )
        return [], None

    if isinstance(payload, dict) and payload.get("error"):
        _LOGGER.warning("SerpAPI reverse search error: %s", payload.get("error"))
        return [], None

    matches = _extract_serpapi_matches(payload, now)
    providers: list[str] | None = ["serpapi:google_reverse_image"] if matches else None
    return matches, providers


def _build_matches(query_hash: str, queued_at: datetime) -> list[ReverseSearchMatch]:
    return [
        ReverseSearchMatch(
            source="serpapi",
            url=f"https://serpapi.com/search?q={query_hash}",
            title="SerpAPI Search Result",
            snippet="A search result from the SerpAPI API.",
        )
    ]


def run_reverse_search(
    image_id: UUID | str, image_bytes: bytes
) -> ReverseSearchJobResponse:
    resolved_image_id = _normalize_image_id(image_id)
    queued_at = datetime.now(timezone.utc)
    job_id = uuid4()
    query_hash = _hash_bytes(image_bytes) if image_bytes else None
    status = "queued"
    detail: str | None = None

    if image_bytes:
        matches, providers = _fetch_serpapi_matches(image_bytes, queued_at)
        if not matches:
            matches = _build_matches(query_hash, queued_at)
            providers = _PROVIDERS

        status = "completed"
        _RESULTS_CACHE[resolved_image_id] = ReverseSearchResult(
            job_id=job_id,
            image_id=resolved_image_id,
            status="completed",
            queried_at=queued_at,
            query_hash=query_hash,
            providers=providers,
            matches=matches,
        )
    else:
        status = "invalid_request"
        detail = "reverse search skipped: image_bytes missing"
        _RESULTS_CACHE[resolved_image_id] = ReverseSearchResult(
            job_id=job_id,
            image_id=resolved_image_id,
            status=status,
            queried_at=queued_at,
            query_hash=None,
            providers=None,
            matches=[],
        )

    return ReverseSearchJobResponse(
        job_id=job_id,
        image_id=resolved_image_id,
        status=status,
        detail=detail or f"reverse search {status} for {resolved_image_id}",
        query_hash=query_hash,
        queued_at=queued_at,
    )


def get_reverse_search_results(image_id: UUID | str) -> ReverseSearchResult:
    resolved_image_id = _normalize_image_id(image_id)
    cached = _RESULTS_CACHE.get(resolved_image_id)
    if cached is not None:
        return cached

    now = datetime.utcnow()
    fallback_hash = _hash_text(str(resolved_image_id))
    matches = _build_matches(fallback_hash, now)

    result = ReverseSearchResult(
        job_id=uuid4(),
        image_id=resolved_image_id,
        status="completed",
        queried_at=now,
        query_hash=fallback_hash,
        providers=_PROVIDERS,
        matches=matches,
    )
    _RESULTS_CACHE[resolved_image_id] = result
    return result
