from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID, uuid4

from app.schemas.provenance import ProvenanceBlock, ProvenanceChainResponse


@dataclass(frozen=True)
class Observation:
    observation_type: str
    observation_data: dict[str, Any]


def _hash_block(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(serialized).hexdigest()


def _build_block(
    *,
    image_id: UUID,
    chain_id: UUID,
    block_number: int,
    previous_hash: str | None,
    observation: Observation,
    recorded_at: datetime,
) -> ProvenanceBlock:
    payload = {
        "image_id": str(image_id),
        "chain_id": str(chain_id),
        "block_number": block_number,
        "previous_hash": previous_hash,
        "observation_type": observation.observation_type,
        "observation_data": observation.observation_data,
        "recorded_at": recorded_at.isoformat() + "Z",
    }
    return ProvenanceBlock(
        block_number=block_number,
        previous_hash=previous_hash,
        block_hash=_hash_block(payload),
        observation_type=observation.observation_type,
        observation_data=observation.observation_data,
        recorded_at=recorded_at,
    )


def build_provenance_chain(
    image_id: UUID,
    observations: list[Observation] | None = None,
) -> ProvenanceChainResponse:
    chain_id = uuid4()
    created_at = datetime.utcnow()
    default_observations = observations or [
        Observation(
            observation_type="image_submission",
            observation_data={"image_id": str(image_id), "source": "ingestion"},
        ),
        Observation(
            observation_type="reverse_search",
            observation_data={"matches_found": 0, "sources": []},
        ),
        Observation(
            observation_type="forensics",
            observation_data={"anomaly_score": 0.12, "signals": []},
        ),
        Observation(
            observation_type="provenance_snapshot",
            observation_data={"consensus": "emerging", "cluster_count": 1},
        ),
    ]

    blocks: list[ProvenanceBlock] = []
    previous_hash: str | None = None
    for index, observation in enumerate(default_observations):
        recorded_at = datetime.utcnow()
        block = _build_block(
            image_id=image_id,
            chain_id=chain_id,
            block_number=index,
            previous_hash=previous_hash,
            observation=observation,
            recorded_at=recorded_at,
        )
        blocks.append(block)
        previous_hash = block.block_hash

    return ProvenanceChainResponse(
        chain_id=chain_id,
        image_id=image_id,
        status="completed",
        created_at=created_at,
        blocks=blocks,
    )


def build_provenance(
    image_id: UUID, image_bytes: bytes | None = None
) -> ProvenanceChainResponse:
    image_hash = None
    if image_bytes:
        image_hash = hashlib.sha256(image_bytes).hexdigest()
    observations = [
        Observation(
            observation_type="image_submission",
            observation_data={
                "image_id": str(image_id),
                "source": "ingestion",
                "image_hash": image_hash,
            },
        )
    ]
    return build_provenance_chain(image_id=image_id, observations=observations)
