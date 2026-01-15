from uuid import UUID, uuid4

from fastapi import APIRouter

from app.schemas.common import JobResponse

router = APIRouter()


@router.post("/build-chain/{image_id}", response_model=JobResponse)
async def build_provenance_chain(image_id: UUID) -> JobResponse:
    return JobResponse(job_id=uuid4(), detail=f"provenance build queued for {image_id}")


@router.get("/chain/{image_id}", response_model=JobResponse)
async def get_provenance_chain(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"chain ready for {image_id}"
    )


@router.get("/genealogy/{image_id}", response_model=JobResponse)
async def get_genealogical_tree(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"genealogy ready for {image_id}"
    )
