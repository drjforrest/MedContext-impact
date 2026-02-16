"""Shared orchestrator utilities."""

from __future__ import annotations

import json
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def parse_force_tools(raw: str | None) -> list[str]:
    """Parse force_tools from a comma-separated string or JSON array.

    Accepts: "forensics,provenance" or '["forensics","provenance"]'
    Filters against the live set of enabled add-on modules from settings, so
    a tool that is not enabled is silently dropped (the agent layer also enforces this).
    """
    if not raw or not raw.strip():
        return []
    stripped = raw.strip()
    if stripped.startswith("["):
        try:
            parsed = json.loads(stripped)
            names = (
                [t for t in parsed if isinstance(t, str)]
                if isinstance(parsed, list)
                else []
            )
        except json.JSONDecodeError:
            logger.warning("force_tools JSON parse error: %r", stripped)
            names = []
    else:
        names = [t.strip() for t in stripped.split(",") if t.strip()]
    enabled_set = set(settings.get_enabled_addons())
    return [t for t in names if t in enabled_set]


def merge_tools(
    agentic_tools: list[str],
    forced_tools: list[str],
) -> list[str]:
    """Merge agentic-selected and user-forced tool lists.

    Agentic tools appear first; forced tools are appended if not already present.
    Deduplication preserves insertion order.

    Args:
        agentic_tools: Tools selected by the AI triage/orchestration step.
        forced_tools:  Tools the user explicitly requested regardless of triage.

    Returns:
        Ordered, deduplicated list with agentic tools first.
    """
    merged = list(dict.fromkeys(agentic_tools + forced_tools))
    if forced_tools:
        logger.info(
            "Tool override: user forced %s; agentic selected %s; running %s",
            forced_tools,
            agentic_tools,
            merged,
        )
    return merged
