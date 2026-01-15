from uuid import UUID, uuid4

from fastapi import APIRouter

from app.provenance.service import build_provenance_chain
from app.schemas.common import JobResponse
from app.schemas.provenance import ProvenanceChainResponse

router = APIRouter()


@router.post("/build-chain/{image_id}", response_model=ProvenanceChainResponse)
async def build_provenance_chain_endpoint(image_id: UUID) -> ProvenanceChainResponse:
    return build_provenance_chain(image_id)


@router.get("/chain/{image_id}", response_model=ProvenanceChainResponse)
async def get_provenance_chain(image_id: UUID) -> ProvenanceChainResponse:
    return build_provenance_chain(image_id)


@router.get("/genealogy/{image_id}", response_model=JobResponse)
async def get_genealogical_tree(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"genealogy ready for {image_id}"
    )
