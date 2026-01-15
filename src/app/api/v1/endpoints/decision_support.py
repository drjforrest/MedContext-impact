from uuid import UUID, uuid4

from fastapi import APIRouter, Query

from app.metrics.integrity import IntegrityWeights, compute_integrity_score
from app.schemas.common import IntegrityScoreResponse, IntegrityWeightsResponse, JobResponse

router = APIRouter()


@router.post("/assess/{image_id}", response_model=JobResponse)
async def assess_image(image_id: UUID) -> JobResponse:
    return JobResponse(job_id=uuid4(), detail=f"assessment queued for {image_id}")


@router.get("/recommendation/{image_id}", response_model=JobResponse)
async def get_recommendation(
    image_id: UUID, audience: str = Query("general")
) -> JobResponse:
    return JobResponse(
        job_id=uuid4(),
        status="completed",
        detail=f"recommendation ready for {image_id} ({audience})",
    )


@router.get("/summary/{image_id}", response_model=JobResponse)
async def get_executive_summary(image_id: UUID) -> JobResponse:
    return JobResponse(
        job_id=uuid4(), status="completed", detail=f"summary ready for {image_id}"
    )


@router.get("/integrity-score", response_model=IntegrityScoreResponse)
async def get_integrity_score(
    plausibility: float | None = Query(default=None, ge=0, le=1),
    genealogy_consistency: float | None = Query(default=None, ge=0, le=1),
    source_reputation: float | None = Query(default=None, ge=0, le=1),
    weight_plausibility: float | None = Query(default=None, ge=0),
    weight_genealogy: float | None = Query(default=None, ge=0),
    weight_source: float | None = Query(default=None, ge=0),
) -> IntegrityScoreResponse:
    default_weights = IntegrityWeights()
    weights = IntegrityWeights(
        plausibility=(
            weight_plausibility
            if weight_plausibility is not None
            else default_weights.plausibility
        ),
        genealogy_consistency=(
            weight_genealogy
            if weight_genealogy is not None
            else default_weights.genealogy_consistency
        ),
        source_reputation=(
            weight_source
            if weight_source is not None
            else default_weights.source_reputation
        ),
    )
    score = compute_integrity_score(
        plausibility=plausibility,
        genealogy_consistency=genealogy_consistency,
        source_reputation=source_reputation,
        weights=weights,
    )
    return IntegrityScoreResponse(
        plausibility=plausibility,
        genealogy_consistency=genealogy_consistency,
        source_reputation=source_reputation,
        weights=IntegrityWeightsResponse(
            plausibility=weights.plausibility,
            genealogy_consistency=weights.genealogy_consistency,
            source_reputation=weights.source_reputation,
        ),
        score=score,
    )
