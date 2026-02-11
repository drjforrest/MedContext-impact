from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.modules import require_module
from app.db.models import ImageSubmission
from app.db.session import get_db
from app.provenance.blockchain import get_blockchain_anchor_service
from app.provenance.service import build_provenance, get_provenance_manifest
from app.provenance.service import store_provenance_manifest
from app.schemas.common import JobResponse
from app.schemas.provenance import (
    ProvenanceChainResponse,
    ProvenanceManifestCreate,
    ProvenanceManifestResponse,
)

router = APIRouter(dependencies=[Depends(require_module("provenance"))])


def _build_manifest_response(record) -> ProvenanceManifestResponse:
    return ProvenanceManifestResponse(
        id=record.id,
        image_id=record.image_id,
        image_hash=record.image_hash,
        manifest_label=record.manifest_label,
        manifest_json=record.manifest_json,
        signature_status=record.signature_status,
        validation_state=record.validation_state,
        validation_results=record.validation_results,
        source_url=record.source_url,
        created_at=record.created_at,
    )


def _validate_image_hash(image_hash: str) -> None:
    if len(image_hash) != 64 or any(ch not in "0123456789abcdef" for ch in image_hash):
        raise HTTPException(status_code=400, detail="Invalid image hash.")


def _get_image_submission(image_id: UUID, db: Session) -> ImageSubmission:
    submission = (
        db.query(ImageSubmission).filter(ImageSubmission.id == image_id).one_or_none()
    )
    if submission is None:
        raise HTTPException(status_code=404, detail="Image not found.")
    return submission


@router.post("/build-chain/{image_id}", response_model=ProvenanceChainResponse)
async def build_provenance_chain_endpoint(
    image_id: UUID, db: Session = Depends(get_db)
) -> ProvenanceChainResponse:
    submission = _get_image_submission(image_id, db)
    return build_provenance(image_id=image_id, image_hash=submission.image_hash, db=db)


@router.get("/chain/{image_id}", response_model=ProvenanceChainResponse)
async def get_provenance_chain(
    image_id: UUID, db: Session = Depends(get_db)
) -> ProvenanceChainResponse:
    submission = _get_image_submission(image_id, db)
    return build_provenance(image_id=image_id, image_hash=submission.image_hash, db=db)


@router.get("/genealogy/{image_id}", response_model=JobResponse)
async def get_genealogical_tree(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"genealogy ready for {image_id}"
    )


@router.post("/manifest", response_model=ProvenanceManifestResponse)
async def create_manifest(
    payload: ProvenanceManifestCreate, db: Session = Depends(get_db)
) -> ProvenanceManifestResponse:
    _validate_image_hash(payload.image_hash)
    record = store_provenance_manifest(
        db,
        image_hash=payload.image_hash,
        manifest_json=payload.manifest_json,
        source_url=payload.source_url,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _build_manifest_response(record)


@router.get("/manifest/{image_hash}", response_model=ProvenanceManifestResponse)
async def get_manifest(
    image_hash: str, db: Session = Depends(get_db)
) -> ProvenanceManifestResponse:
    _validate_image_hash(image_hash)
    record = get_provenance_manifest(db, image_hash=image_hash)
    if record is None:
        raise HTTPException(status_code=404, detail="Manifest not found.")
    return _build_manifest_response(record)


@router.get("/verify/{image_hash}/blockchain")
async def blockchain_verify(image_hash: str) -> dict:
    """
    Query the Polygon smart contract for provenance records for this image hash.

    Returns the full on-chain history with timestamps, recorder addresses,
    and a PolygonScan verification URL.
    """
    _validate_image_hash(image_hash)
    anchor_service = get_blockchain_anchor_service()
    if anchor_service is None:
        raise HTTPException(
            status_code=503,
            detail="Blockchain anchoring is not enabled or not configured.",
        )
    result = anchor_service.verify_on_chain(image_hash)
    if not result["verified"]:
        raise HTTPException(
            status_code=404,
            detail="No on-chain provenance records found for this image hash.",
        )
    return result
