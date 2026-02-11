from fastapi import APIRouter

from app.api.v1.endpoints import (
    analysis,
    forensics,
    ingestion,
    orchestrator,
    provenance,
    reverse_search,
    semantic,
)

api_router = APIRouter()
api_router.include_router(ingestion.router, prefix="/ingest", tags=["ingestion"])
api_router.include_router(analysis.router, prefix="/analyze", tags=["analysis"])
api_router.include_router(
    reverse_search.router, prefix="/reverse-search", tags=["reverse-search"]
)
api_router.include_router(semantic.router, prefix="/semantic", tags=["semantic"])
api_router.include_router(
    orchestrator.router, prefix="/orchestrator", tags=["orchestrator"]
)
api_router.include_router(forensics.router, prefix="/forensics", tags=["forensics"])
api_router.include_router(provenance.router, prefix="/provenance", tags=["provenance"])
