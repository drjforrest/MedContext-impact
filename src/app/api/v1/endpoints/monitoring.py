from typing import Any

from fastapi import APIRouter

from app.monitoring.service import ingest_monitoring_payload
from app.schemas.monitoring import MonitoringIngestResponse

router = APIRouter()


@router.post("/ingest", response_model=MonitoringIngestResponse)
async def ingest_monitoring(payload: dict[str, Any]) -> MonitoringIngestResponse:
    return ingest_monitoring_payload(payload)
