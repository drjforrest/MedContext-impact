from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class FacebookIngestResult:
    status: str
    detail: str
    metadata: dict[str, Any]


def ingest_post(payload: dict[str, Any]) -> FacebookIngestResult:
    """Placeholder for Facebook post ingestion."""
    return FacebookIngestResult(
        status="accepted",
        detail="facebook payload accepted (stub)",
        metadata={"payload_keys": list(payload.keys())},
    )
