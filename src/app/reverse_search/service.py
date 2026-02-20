"""Reverse image search using Google Cloud Vision API Web Detection.

Sends raw image bytes to the Vision API and returns three match types:
  - Full page matches (pages_with_matching_images)
  - Partial / visually similar matches (partially_matching_images)
  - Named web entities (web_entities with confidence > 0.5)

Results are cached in-memory (TTLCache, 1 hour, max 1024 entries).
The google-cloud-vision package is optional; when absent the search
returns an empty match list and logs a warning.
"""

from __future__ import annotations

import hashlib
import logging
import tempfile
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4
from urllib.parse import quote_plus

import cachetools

from app.core.config import settings
from app.core.utils import resize_image


try:
    from google.cloud import vision  # type: ignore[attr-defined]
except ImportError:
    vision = None  # type: ignore[assignment]

try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None
from app.schemas.reverse_search import (
    ReverseSearchJobResponse,
    ReverseSearchMatch,
    ReverseSearchResult,
)

_LOGGER = logging.getLogger(__name__)
_PROVIDERS = ["google_vision", "serpapi"]
_RESULTS_CACHE: cachetools.TTLCache[UUID, ReverseSearchResult] = cachetools.TTLCache(
    maxsize=1024,
    ttl=3600,
)


def _normalize_image_id(image_id: UUID | str) -> UUID:
    if isinstance(image_id, UUID):
        return image_id
    try:
        return UUID(str(image_id))
    except ValueError:
        # If not a valid UUID, create a deterministic UUID from the string
        import hashlib

        hash_bytes = hashlib.md5(str(image_id).encode()).digest()
        return UUID(bytes=hash_bytes[:16])


def _hash_bytes(image_bytes: bytes) -> str:
    return hashlib.sha256(image_bytes).hexdigest()


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _resize_image(image_bytes: bytes, max_size: int = 1024) -> bytes:
    """Resize image to reduce latency and avoid API limits."""
    return resize_image(image_bytes, max_size=max_size, quality=85)


def _reverse_search_with_google_vision(image_bytes: bytes) -> list[ReverseSearchMatch]:
    """
    Google Vision API accepts image bytes directly - no URL needed.

    Privacy: Image sent directly to Google's API over HTTPS, not stored publicly.
    Cost: $1.50 per 1000 images (Web Detection feature).
    """
    if vision is None:
        _LOGGER.warning("google-cloud-vision not installed; skipping Vision API search")
        return []
    try:
        client = vision.ImageAnnotatorClient()

        # Send raw image bytes to Google Vision
        image = vision.Image(content=image_bytes)

        response = client.web_detection(image=image)
        web_detection = response.web_detection

        if response.error.message:
            _LOGGER.error(f"Google Vision API error: {response.error.message}")
            return []

        matches = []

        # Extract full matching images
        for page in web_detection.pages_with_matching_images[:10]:
            matches.append(
                ReverseSearchMatch(
                    source="google_vision",
                    url=page.url,
                    title=page.page_title or "Image match found",
                    snippet=f"Full image match discovered at {page.url}",
                    confidence=0.95,
                    discovered_at=datetime.now(timezone.utc),
                    metadata={
                        "match_type": "full",
                        "page_url": page.url,
                        "score": getattr(page, "score", None),
                    },
                )
            )

        # Extract partial matches (visually similar)
        for partial in web_detection.partially_matching_images[:10]:
            matches.append(
                ReverseSearchMatch(
                    source="google_vision",
                    url=partial.url,
                    title="Partial match",
                    snippet="Visually similar image found",
                    confidence=0.70,
                    discovered_at=datetime.now(timezone.utc),
                    metadata={
                        "match_type": "partial",
                        "page_url": partial.url,
                        "score": getattr(partial, "score", None),
                    },
                )
            )

        # Extract web entities (what Google thinks the image represents)
        for entity in web_detection.web_entities:
            if entity.score > 0.5:
                matches.append(
                    ReverseSearchMatch(
                        source="google_vision",
                        url=f"https://www.google.com/search?q={quote_plus(entity.description or 'medical image')}",
                        title=f"Related: {entity.description or 'Medical Subject'}",
                        snippet=f"Entity confidence: {entity.score:.2f}",
                        confidence=entity.score,
                        discovered_at=datetime.now(timezone.utc),
                        metadata={
                            "match_type": "entity",
                            "entity_id": entity.entity_id,
                        },
                    )
                )

        return matches
    except Exception as e:
        _LOGGER.error(f"Google Vision API error: {e}")
        return []


def _reverse_search_with_serpapi(
    image_bytes: bytes, source_url: str | None = None
) -> list[ReverseSearchMatch]:
    """
    Reverse image search via SerpAPI (Google Lens engine).

    SerpAPI supports both direct URLs and local file uploads.
    Privacy: Image is uploaded to SerpAPI's servers for processing.
    Cost: Requires SerpAPI subscription/credits.
    """
    if not settings.serp_api_key:
        _LOGGER.warning("SERP_API_KEY missing; skipping SerpAPI search")
        return []

    if GoogleSearch is None:
        _LOGGER.warning("google-search-results not installed; skipping SerpAPI search")
        return []

    try:
        params: dict[str, Any] = {
            "engine": "google_lens",
            "api_key": settings.serp_api_key,
        }

        # If we have a source URL, use it directly (faster, no upload needed)
        if source_url:
            params["url"] = source_url
            _LOGGER.info(f"SerpAPI: searching via URL: {source_url}")
            search = GoogleSearch(params)
            results = search.get_dict()
        else:
            # Upload local bytes via temporary file
            import os
            import requests

            fd, tf_path = tempfile.mkstemp(suffix=".jpg")
            try:
                with os.fdopen(fd, "wb") as tf:
                    tf.write(image_bytes)

                _LOGGER.info(f"SerpAPI: searching via local file upload: {tf_path}")

                # The google-search-results library (v2.4.2) uses requests.get internally
                # and doesn't support file uploads. We must use requests.post directly.
                with open(tf_path, "rb") as f:
                    post_data = {
                        "engine": "google_lens",
                        "api_key": settings.serp_api_key,
                        "source": "python",
                        "output": "json",
                    }
                    files = {"file": f}
                    _LOGGER.info(
                        "SerpAPI: sending multipart POST request to https://serpapi.com/search"
                    )
                    response = requests.post(
                        "https://serpapi.com/search",
                        data=post_data,
                        files=files,
                        timeout=60,
                    )
                    response.raise_for_status()
                    results = response.json()
            finally:
                if os.path.exists(tf_path):
                    os.unlink(tf_path)

        matches = []

        # Extract visual matches from Google Lens results
        visual_matches = results.get("visual_matches", [])
        for match in visual_matches[:10]:
            match_url = match.get("link") or match.get("url")
            if not match_url:
                continue

            matches.append(
                ReverseSearchMatch(
                    source="serpapi:google_lens",
                    url=match_url,
                    title=match.get("title") or "Visual match",
                    snippet=match.get("source") or match.get("snippet"),
                    confidence=0.85,  # SerpAPI doesn't always provide a float score here
                    discovered_at=datetime.now(timezone.utc),
                    metadata={
                        "thumbnail": match.get("thumbnail"),
                        "price": match.get("price"),
                    },
                )
            )

        # Extract Knowledge Graph info if available (high confidence identification)
        knowledge_graph = results.get("knowledge_graph", [])
        if isinstance(knowledge_graph, list) and knowledge_graph:
            for item in knowledge_graph:
                matches.append(
                    ReverseSearchMatch(
                        source="serpapi:knowledge_graph",
                        url=item.get("link", "https://google.com"),
                        title=item.get("title"),
                        snippet=item.get("subtitle")
                        or "Knowledge Graph identification",
                        confidence=0.95,
                        discovered_at=datetime.now(timezone.utc),
                        metadata={"type": "knowledge_graph"},
                    )
                )
        elif isinstance(knowledge_graph, dict):
            matches.append(
                ReverseSearchMatch(
                    source="serpapi:knowledge_graph",
                    url=knowledge_graph.get("link", "https://google.com"),
                    title=knowledge_graph.get("title"),
                    snippet=knowledge_graph.get("subtitle")
                    or "Knowledge Graph identification",
                    confidence=0.95,
                    discovered_at=datetime.now(timezone.utc),
                    metadata={"type": "knowledge_graph"},
                )
            )

        return matches
    except Exception as e:
        _LOGGER.error(f"SerpAPI error: {e}")
        return []


def run_reverse_search(
    image_id: UUID | str, image_bytes: bytes, source_url: str | None = None
) -> ReverseSearchJobResponse:
    resolved_image_id = _normalize_image_id(image_id)
    queued_at = datetime.now(timezone.utc)
    job_id = uuid4()
    query_hash = _hash_bytes(image_bytes) if image_bytes else None
    status = "queued"
    detail: str | None = None

    matches = []
    used_providers = []

    if image_bytes or source_url:
        # Resize image once if bytes are present
        processed_bytes = _resize_image(image_bytes) if image_bytes else None

        # 1. Try SerpAPI first if key is present (often more descriptive for generic objects)
        if settings.serp_api_key:
            # Pass processed_bytes or None
            serp_matches = _reverse_search_with_serpapi(
                processed_bytes or b"", source_url
            )
            if serp_matches:
                matches.extend(serp_matches)
                used_providers.append("serpapi")

        # 2. Try Google Vision if enabled and we have bytes
        if processed_bytes and vision is not None:
            gv_matches = _reverse_search_with_google_vision(processed_bytes)
            if gv_matches:
                matches.extend(gv_matches)
                used_providers.append("google_vision")

        if matches:
            status = "completed"
            detail = f"Found {len(matches)} matches via {', '.join(used_providers)}"
        else:
            status = "completed"
            detail = "No matches found via available providers"

        _RESULTS_CACHE[resolved_image_id] = ReverseSearchResult(
            job_id=job_id,
            image_id=resolved_image_id,
            status=status,
            queried_at=queued_at,
            query_hash=query_hash,
            providers=used_providers if used_providers else None,
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

    now = datetime.now(timezone.utc)
    fallback_hash = _hash_text(str(resolved_image_id))

    result = ReverseSearchResult(
        job_id=uuid4(),
        image_id=resolved_image_id,
        status="completed",
        queried_at=now,
        query_hash=fallback_hash,
        providers=_PROVIDERS,
        matches=[],
    )
    _RESULTS_CACHE[resolved_image_id] = result
    return result
