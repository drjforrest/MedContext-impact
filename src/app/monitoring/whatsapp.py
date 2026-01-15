from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class WhatsAppIngestResult:
    status: str
    detail: str
    metadata: dict[str, Any]


def process_webhook(payload: dict[str, Any]) -> WhatsAppIngestResult:
    """Placeholder for WhatsApp webhook processing."""
    return WhatsAppIngestResult(
        status="accepted",
        detail="whatsapp payload accepted (stub)",
        metadata={"payload_keys": list(payload.keys())},
    )
