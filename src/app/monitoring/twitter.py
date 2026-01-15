from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TwitterIngestResult:
    status: str
    detail: str
    metadata: dict[str, Any]


def ingest_tweet(payload: dict[str, Any]) -> TwitterIngestResult:
    """Placeholder for Twitter/X ingestion."""
    return TwitterIngestResult(
        status="accepted",
        detail="twitter payload accepted (stub)",
        metadata={"payload_keys": list(payload.keys())},
    )
