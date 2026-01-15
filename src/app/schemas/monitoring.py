from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel


class MonitoringIngestResponse(BaseModel):
    status: str
    detail: Optional[str] = None
    metadata: dict[str, Any]
