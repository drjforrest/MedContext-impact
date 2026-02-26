"""Analytics API for run metrics."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.service import get_analytics_stats
from app.db.session import get_db

router = APIRouter()


@router.get("/stats")
def get_stats(
    days: int = Query(default=30, ge=1, le=365),
    db: Session = Depends(get_db),
) -> dict:
    """
    Get aggregated run analytics.

    Access from your laptop: curl http://localhost:8000/api/v1/analytics/stats
    Or from deployed: curl https://medcontext.drjforrest.com/api/v1/analytics/stats
    """
    return get_analytics_stats(db, days=days)
