from fastapi import APIRouter

from app.schemas.claims import (
    ClaimClusterRequest,
    ClaimClusterResponse,
    ClaimExtractionRequest,
    ClaimExtractionResponse,
)
from app.semantic.service import cluster_claims, extract_claims

router = APIRouter()


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
