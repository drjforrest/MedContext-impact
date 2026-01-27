from __future__ import annotations

import hashlib
import io
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from c2pa import C2paError, Reader
from PIL import Image
from sqlalchemy.orm import Session

from app.db.models.provenance import ProvenanceBlock as ProvenanceBlockModel
from app.db.models.provenance import ProvenanceManifest
from app.db.session import SessionLocal
from app.schemas.provenance import ProvenanceBlock, ProvenanceChainResponse

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Observation:
    observation_type: str
    observation_data: dict[str, Any]


@dataclass(frozen=True)
class C2paReadResult:
    manifest_store: dict[str, Any] | None
    active_manifest: dict[str, Any] | None
    active_label: str | None
    validation_state: str | None
    validation_results: dict[str, Any] | None


def _hash_block(payload: dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return hashlib.sha256(serialized).hexdigest()


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


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
        "recorded_at": _format_timestamp(recorded_at),
    }
    return ProvenanceBlock(
        block_number=block_number,
        previous_hash=previous_hash,
        block_hash=_hash_block(payload),
        observation_type=observation.observation_type,
        observation_data=observation.observation_data,
        recorded_at=recorded_at,
    )


def _infer_mime_type(image_bytes: bytes) -> str | None:
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            detected = (image.format or "").lower()
    except Exception:
        return None
    if not detected:
        return None
    if detected == "jpg":
        detected = "jpeg"
    return f"image/{detected}"


def _read_c2pa(
    image_bytes: bytes, manifest_data: dict[str, Any] | str | None = None
) -> C2paReadResult | None:
    mime_type = _infer_mime_type(image_bytes)
    if not mime_type:
        return None
    payload = None
    if manifest_data is not None:
        payload = (
            manifest_data
            if isinstance(manifest_data, str)
            else json.dumps(manifest_data)
        )
    try:
        with Reader(
            mime_type, io.BytesIO(image_bytes), manifest_data=payload
        ) as reader:
            manifest_store = None
            raw_json = reader.json()
            if raw_json:
                manifest_store = json.loads(raw_json)
            active_manifest = reader.get_active_manifest()
            active_label = None
            if isinstance(manifest_store, dict):
                active_label = manifest_store.get("active_manifest")
            return C2paReadResult(
                manifest_store=manifest_store,
                active_manifest=active_manifest,
                active_label=active_label,
                validation_state=reader.get_validation_state(),
                validation_results=reader.get_validation_results(),
            )
    except C2paError as exc:
        logger.info("C2PA read failed: %s", exc)
    except Exception as exc:
        logger.exception("Unexpected C2PA read error: %s", exc)
    return None


def _normalize_signature_status(validation_state: str | None) -> str:
    if not validation_state:
        return "unknown"
    state = validation_state.lower()
    if state in {"valid", "trusted", "success", "succeeded"}:
        return "valid"
    if state in {"invalid", "untrusted", "failed", "error"}:
        return "invalid"
    return "unknown"


def _get_or_create_manifest(
    db: Session,
    *,
    image_hash: str,
    image_id: UUID | None,
) -> ProvenanceManifest:
    record = (
        db.query(ProvenanceManifest)
        .filter(ProvenanceManifest.image_hash == image_hash)
        .one_or_none()
    )
    if record is None:
        record = ProvenanceManifest(image_hash=image_hash, image_id=image_id)
        db.add(record)
        db.flush()
    elif image_id and record.image_id is None:
        record.image_id = image_id
    return record


def store_provenance_manifest(
    db: Session,
    *,
    image_hash: str,
    image_id: UUID | None = None,
    manifest_json: dict[str, Any] | None = None,
    source_url: str | None = None,
) -> ProvenanceManifest:
    record = _get_or_create_manifest(db, image_hash=image_hash, image_id=image_id)
    if manifest_json is not None:
        record.manifest_json = manifest_json
        if isinstance(manifest_json, dict):
            record.manifest_label = manifest_json.get("active_manifest")
    if source_url:
        record.source_url = source_url
    return record


def get_provenance_manifest(
    db: Session, *, image_hash: str
) -> ProvenanceManifest | None:
    return (
        db.query(ProvenanceManifest)
        .filter(ProvenanceManifest.image_hash == image_hash)
        .one_or_none()
    )


def _materialize_blocks(
    db: Session | None,
    *,
    manifest_record: ProvenanceManifest | None,
    image_id: UUID,
    observations: list[Observation],
    chain_id: UUID | None = None,
) -> tuple[UUID, list[ProvenanceBlock]]:
    if chain_id is None:
        chain_id = uuid4()
    if manifest_record and db is not None:
        existing = (
            db.query(ProvenanceBlockModel)
            .filter(ProvenanceBlockModel.manifest_id == manifest_record.id)
            .order_by(ProvenanceBlockModel.block_number.asc())
            .all()
        )
        if existing:
            return chain_id, [
                ProvenanceBlock(
                    block_number=block.block_number,
                    previous_hash=block.previous_hash,
                    block_hash=block.block_hash,
                    observation_type=block.observation_type,
                    observation_data=block.observation_data,
                    recorded_at=block.recorded_at,
                )
                for block in existing
            ]
    blocks: list[ProvenanceBlock] = []
    previous_hash: str | None = None
    for index, observation in enumerate(observations):
        recorded_at = datetime.now(timezone.utc)
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
        if manifest_record and db is not None:
            db.add(
                ProvenanceBlockModel(
                    manifest_id=manifest_record.id,
                    block_number=block.block_number,
                    previous_hash=block.previous_hash,
                    block_hash=block.block_hash,
                    observation_type=block.observation_type,
                    observation_data=block.observation_data,
                    recorded_at=block.recorded_at,
                )
            )
    return chain_id, blocks


def build_provenance(
    image_id: UUID | str,
    *,
    image_bytes: bytes | None = None,
    image_hash: str | None = None,
    db: Session | None = None,
) -> ProvenanceChainResponse:
    try:
        resolved_image_id = (
            image_id if isinstance(image_id, UUID) else UUID(str(image_id))
        )
    except ValueError as e:
        raise ValueError(f"Invalid image_id format: {image_id}") from e
    if not image_hash and image_bytes:
        image_hash = hashlib.sha256(image_bytes).hexdigest()
    if not image_hash:
        raise ValueError("image_hash is required to build provenance.")

    owns_session = db is None
    session = db or SessionLocal()
    manifest_record = None
    c2pa_result = None
    try:
        manifest_record = (
            session.query(ProvenanceManifest)
            .filter(ProvenanceManifest.image_hash == image_hash)
            .one_or_none()
        )
        if image_bytes:
            c2pa_result = _read_c2pa(image_bytes)
        if c2pa_result and c2pa_result.active_manifest:
            manifest_record = _get_or_create_manifest(
                session, image_hash=image_hash, image_id=resolved_image_id
            )
            manifest_record.manifest_json = c2pa_result.manifest_store
            manifest_record.manifest_label = c2pa_result.active_label
            manifest_record.validation_state = c2pa_result.validation_state
            manifest_record.validation_results = c2pa_result.validation_results
            manifest_record.signature_status = _normalize_signature_status(
                c2pa_result.validation_state
            )
        elif manifest_record and image_bytes and manifest_record.manifest_json:
            c2pa_result = _read_c2pa(
                image_bytes, manifest_data=manifest_record.manifest_json
            )
            if c2pa_result:
                manifest_record.validation_state = c2pa_result.validation_state
                manifest_record.validation_results = c2pa_result.validation_results
                manifest_record.signature_status = _normalize_signature_status(
                    c2pa_result.validation_state
                )

        observations = [
            Observation(
                observation_type="image_submission",
                observation_data={
                    "image_id": str(resolved_image_id),
                    "source": "ingestion",
                    "image_hash": image_hash,
                },
            )
        ]
        if manifest_record:
            observations.append(
                Observation(
                    observation_type="provenance_repository",
                    observation_data={
                        "manifest_label": manifest_record.manifest_label,
                        "signature_status": manifest_record.signature_status,
                    },
                )
            )
        if c2pa_result and c2pa_result.active_manifest:
            observations.append(
                Observation(
                    observation_type="c2pa_manifest",
                    observation_data={
                        "label": c2pa_result.active_label,
                        "embedded": True,
                    },
                )
            )
        if c2pa_result and c2pa_result.validation_state:
            observations.append(
                Observation(
                    observation_type="c2pa_validation",
                    observation_data={
                        "validation_state": c2pa_result.validation_state,
                        "signature_status": _normalize_signature_status(
                            c2pa_result.validation_state
                        ),
                    },
                )
            )

        chain_id = uuid4()
        chain_id, blocks = _materialize_blocks(
            session,
            manifest_record=manifest_record,
            image_id=resolved_image_id,
            observations=observations,
            chain_id=chain_id,
        )

        status = "not_found"
        if c2pa_result and c2pa_result.validation_state:
            signature_status = _normalize_signature_status(c2pa_result.validation_state)
            status = "verified" if signature_status == "valid" else "unverified"
        elif manifest_record:
            status = "registered"

        if owns_session:
            session.commit()

        return ProvenanceChainResponse(
            chain_id=chain_id,
            image_id=resolved_image_id,
            status=status,
            created_at=datetime.now(timezone.utc),
            blocks=blocks,
        )
    finally:
        if owns_session:
            session.close()
