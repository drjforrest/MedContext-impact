from __future__ import annotations

from typing import Any

from app.monitoring.facebook import ingest_post
from app.monitoring.twitter import ingest_tweet
from app.monitoring.whatsapp import process_webhook
from app.schemas.monitoring import MonitoringIngestResponse


def ingest_monitoring_payload(payload: dict[str, Any]) -> MonitoringIngestResponse:
    """Route payloads to platform-specific stubs."""
    source = str(payload.get("source", "unknown")).lower()
    if source == "whatsapp":
        result = process_webhook(payload)
    elif source == "facebook":
        result = ingest_post(payload)
    elif source in {"twitter", "x"}:
        result = ingest_tweet(payload)
    else:
        return MonitoringIngestResponse(
            status="rejected",
            detail="unknown source; expected whatsapp/facebook/twitter/x",
            metadata={"payload_keys": list(payload.keys())},
        )

    return MonitoringIngestResponse(
        status=result.status, detail=result.detail, metadata=result.metadata
    )
