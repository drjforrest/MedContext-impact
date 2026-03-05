"""Analytics API for run metrics."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.analytics.service import get_analytics_stats
from app.db.session import get_db

router = APIRouter()


@router.get("/stats")
def get_stats(
    days: int = Query(default=30, ge=1, le=365),
    all_time: bool = Query(default=False),
    db: Session = Depends(get_db),
) -> dict:
    """Get aggregated run analytics.

    Query params:
      days      — rolling window in days (1–365, default 30). Ignored when all_time=true.
      all_time  — count everything from tracking_start (2026-03-01) onwards.

    From your MacBook:
      curl https://medcontext.drjforrest.com/api/v1/analytics/stats
      curl https://medcontext.drjforrest.com/api/v1/analytics/stats?all_time=true
      curl https://medcontext.drjforrest.com/api/v1/analytics/stats?days=7
    """
    return get_analytics_stats(db, days=days, all_time=all_time)
