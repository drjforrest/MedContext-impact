from uuid import UUID, uuid4

from fastapi import APIRouter

from app.schemas.claims import (
    ClaimClusterRequest,
    ClaimClusterResponse,
    ClaimExtractionRequest,
    ClaimExtractionResponse,
)
from app.schemas.common import JobResponse
from app.semantic.service import cluster_claims, extract_claims

router = APIRouter()


@router.post("/analyze/{image_id}", response_model=JobResponse)
async def analyze_claims(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), detail=f"semantic analysis queued for {image_id}"
    )


@router.get("/clusters/{image_id}", response_model=JobResponse)
async def get_semantic_clusters(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"clusters ready for {image_id}"
    )


@router.post("/claims", response_model=ClaimExtractionResponse)
async def extract_claims_endpoint(
    payload: ClaimExtractionRequest,
) -> ClaimExtractionResponse:
    return extract_claims(payload)


@router.post("/clusters", response_model=ClaimClusterResponse)
async def cluster_claims_endpoint(
    payload: ClaimClusterRequest,
) -> ClaimClusterResponse:
    return cluster_claims(payload)
