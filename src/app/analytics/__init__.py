"""Analytics package."""

from app.analytics.service import get_analytics_stats, record_run_event

__all__ = ["record_run_event", "get_analytics_stats"]
