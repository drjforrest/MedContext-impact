from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel


class ProvenanceBlock(BaseModel):
    block_number: int
    previous_hash: str | None
    block_hash: str
    observation_type: str
    observation_data: dict[str, Any]
    recorded_at: datetime


class ProvenanceChainResponse(BaseModel):
    chain_id: UUID
    image_id: UUID
    status: str
    created_at: datetime
    blocks: list[ProvenanceBlock]
