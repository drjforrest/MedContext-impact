from __future__ import annotations

import base64
import hashlib
import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

import cachetools
from google.cloud import vision

from app.core.config import settings
from app.schemas.reverse_search import (
    ReverseSearchJobResponse,
    ReverseSearchMatch,
    ReverseSearchResult,
)

_LOGGER = logging.getLogger(__name__)
_PROVIDERS = ["google_vision"]
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


def _reverse_search_with_google_vision(image_bytes: bytes) -> list[ReverseSearchMatch]:
    """
    Google Vision API accepts image bytes directly - no URL needed.
    
    Privacy: Image sent directly to Google's API over HTTPS, not stored publicly.
    Cost: $1.50 per 1000 images (Web Detection feature).
    """
    try:
        client = vision.ImageAnnotatorClient()

        # Send raw image bytes to Google Vision
        image = vision.Image(content=image_bytes)

        response = client.web_detection(image=image)
        web_detection = response.web_detection

        matches = []

        # Extract full matching images
        for page in web_detection.pages_with_matching_images[:10]:
            matches.append(ReverseSearchMatch(
                source="google_vision",
                url=page.url,
                title=page.page_title or "Image match found",
                snippet=f"Full image match discovered at {page.url}",
                confidence=0.95,
                discovered_at=datetime.now(timezone.utc),
                metadata={
                    "match_type": "full",
                    "page_url": page.page_url
                }
            ))

        # Extract partial matches (visually similar)
        for partial in web_detection.partially_matching_images[:10]:
            matches.append(ReverseSearchMatch(
                source="google_vision",
                url=partial.url,
                title="Partial match",
                snippet="Visually similar image found",
                confidence=0.70,
                discovered_at=datetime.now(timezone.utc),
                metadata={"match_type": "partial"}
            ))

        # Extract web entities (what Google thinks the image represents)
        for entity in web_detection.web_entities:
            if entity.score > 0.5:
                matches.append(ReverseSearchMatch(
                    source="google_vision",
                    url=f"https://www.google.com/search?q={entity.description}",
                    title=f"Related: {entity.description}",
                    snippet=f"Entity confidence: {entity.score:.2f}",
                    confidence=entity.score,
                    discovered_at=datetime.now(timezone.utc),
                    metadata={
                        "match_type": "entity",
                        "entity_id": entity.entity_id
                    }
                ))

        return matches
    except Exception as e:
        _LOGGER.error(f"Google Vision API error: {e}")
        return []


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
        matches = _reverse_search_with_google_vision(image_bytes)
        providers = _PROVIDERS if matches else None
        
        if matches:
            status = "completed"
            detail = f"Found {len(matches)} matches via Google Vision API"
        else:
            status = "completed"
            detail = "No matches found via Google Vision API"
            
        _RESULTS_CACHE[resolved_image_id] = ReverseSearchResult(
            job_id=job_id,
            image_id=resolved_image_id,
            status=status,
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