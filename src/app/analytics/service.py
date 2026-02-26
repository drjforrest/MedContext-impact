"""Analytics service for recording and querying run metrics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import RunEvent


def record_run_event(
    db: Session,
    *,
    started_at: datetime,
    completed_at: datetime,
    outcome: str,
    source_channel: str,
    verdict: str | None = None,
    error_message: str | None = None,
) -> RunEvent:
    """Record a single run event."""
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)
    event = RunEvent(
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
        outcome=outcome,
        verdict=verdict,
        source_channel=source_channel,
        error_message=error_message,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def get_analytics_stats(
    db: Session,
    *,
    days: int = 30,
) -> dict[str, Any]:
    """Return aggregated analytics for easy access."""
    since = datetime.utcnow() - timedelta(days=days)

    # Total runs
    total = db.scalar(
        select(func.count(RunEvent.id)).where(RunEvent.started_at >= since)
    ) or 0

    # Success/error counts
    outcome_counts = dict(
        db.execute(
            select(RunEvent.outcome, func.count(RunEvent.id))
            .where(RunEvent.started_at >= since)
            .group_by(RunEvent.outcome)
        ).all()
    )
    success_count = outcome_counts.get("success", 0)
    error_count = outcome_counts.get("error", 0)

    # Verdict distribution
    verdict_counts = dict(
        db.execute(
            select(RunEvent.verdict, func.count(RunEvent.id))
            .where(RunEvent.started_at >= since, RunEvent.verdict.isnot(None))
            .group_by(RunEvent.verdict)
        ).all()
    )

    # Avg duration (successful runs only)
    avg_duration = db.scalar(
        select(func.avg(RunEvent.duration_ms))
        .where(
            RunEvent.started_at >= since,
            RunEvent.outcome == "success",
        )
    )
    avg_duration_ms = float(avg_duration) if avg_duration is not None else None

    # Runs per day (last 7 days)
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    runs_per_day = []
    for i in range(7):
        day_start = today - timedelta(days=6 - i)
        day_end = day_start + timedelta(days=1)
        count = db.scalar(
            select(func.count(RunEvent.id)).where(
                RunEvent.started_at >= day_start,
                RunEvent.started_at < day_end,
            )
        ) or 0
        runs_per_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "count": count,
        })

    # Source channel breakdown
    source_counts = dict(
        db.execute(
            select(RunEvent.source_channel, func.count(RunEvent.id))
            .where(RunEvent.started_at >= since)
            .group_by(RunEvent.source_channel)
        ).all()
    )

    return {
        "period_days": days,
        "since": since.isoformat(),
        "total_runs": total,
        "success_count": success_count,
        "error_count": error_count,
        "success_rate": (success_count / total * 100) if total > 0 else None,
        "avg_duration_ms": round(avg_duration_ms, 1) if avg_duration_ms is not None else None,
        "verdict_distribution": verdict_counts,
        "source_distribution": source_counts,
        "runs_per_day": runs_per_day,
    }
