"""Analytics service for recording and querying run metrics."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import RunEvent

# Official start of production tracking. All meaningful data begins here.
TRACKING_START = datetime(2026, 3, 1, 0, 0, 0)


def record_run_event(
    db: Session,
    *,
    started_at: datetime,
    completed_at: datetime,
    outcome: str,
    source_channel: str,
    verdict: str | None = None,
    ip_address: str | None = None,
    error_message: str | None = None,
) -> RunEvent:
    """Record a single run event."""
    delta = completed_at - started_at
    if delta.total_seconds() < 0:
        raise ValueError("completed_at must be >= started_at")
    duration_ms = int(delta.total_seconds() * 1000)
    event = RunEvent(
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=duration_ms,
        outcome=outcome,
        verdict=verdict,
        source_channel=source_channel,
        ip_address=ip_address,
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
    all_time: bool = False,
) -> dict[str, Any]:
    """Return aggregated analytics for easy access.

    Pass all_time=True to count from TRACKING_START (2026-03-01) rather than
    the rolling ``days`` window.
    """
    since = TRACKING_START if all_time else datetime.utcnow() - timedelta(days=days)

    # Total runs
    total = (
        db.scalar(select(func.count(RunEvent.id)).where(RunEvent.started_at >= since))
        or 0
    )

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
        select(func.avg(RunEvent.duration_ms)).where(
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
        count = (
            db.scalar(
                select(func.count(RunEvent.id)).where(
                    RunEvent.started_at >= day_start,
                    RunEvent.started_at < day_end,
                )
            )
            or 0
        )
        runs_per_day.append(
            {
                "date": day_start.strftime("%Y-%m-%d"),
                "count": count,
            }
        )

    # Source channel breakdown
    source_counts = dict(
        db.execute(
            select(RunEvent.source_channel, func.count(RunEvent.id))
            .where(RunEvent.started_at >= since)
            .group_by(RunEvent.source_channel)
        ).all()
    )

    # IP breakdown (top 20 by count)
    ip_counts = dict(
        db.execute(
            select(RunEvent.ip_address, func.count(RunEvent.id))
            .where(RunEvent.started_at >= since, RunEvent.ip_address.isnot(None))
            .group_by(RunEvent.ip_address)
            .order_by(func.count(RunEvent.id).desc())
            .limit(20)
        ).all()
    )

    return {
        "tracking_start": TRACKING_START.date().isoformat(),
        "period_days": None if all_time else days,
        "all_time": all_time,
        "since": since.isoformat(),
        "total_runs": total,
        "success_count": success_count,
        "error_count": error_count,
        "success_rate": (success_count / total * 100) if total > 0 else None,
        "avg_duration_ms": round(avg_duration_ms, 1)
        if avg_duration_ms is not None
        else None,
        "verdict_distribution": verdict_counts,
        "source_distribution": source_counts,
        "ip_distribution": ip_counts,
        "runs_per_day": runs_per_day,
    }
