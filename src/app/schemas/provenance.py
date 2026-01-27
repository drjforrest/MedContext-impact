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


class ProvenanceManifestCreate(BaseModel):
    image_hash: str
    manifest_json: dict[str, Any] | None = None
    source_url: str | None = None


class ProvenanceManifestResponse(BaseModel):
    id: UUID
    image_id: UUID | None
    image_hash: str
    manifest_label: str | None
    manifest_json: dict[str, Any] | None
    signature_status: str | None
    validation_state: str | None
    validation_results: dict[str, Any] | None
    source_url: str | None
    created_at: datetime
