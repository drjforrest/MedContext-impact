"""Runtime provider state singleton.

Tracks the active MedGemma provider, llama-cpp busy state, and BYO GPU credentials
in memory.  No persistence — state resets on process restart, which is intentional
(production server starts clean with llama-cpp as default).
"""

from __future__ import annotations

import threading
import time

# Import settings at module level to avoid importing inside _lock (deadlock risk).
from app.core.config import settings


# ---------------------------------------------------------------------------
# Internal state (module-level singleton — thread-safe via _lock)
# ---------------------------------------------------------------------------

_lock = threading.Lock()

_active_provider: str = "llama_cpp"        # "llama_cpp" | "byo_gpu"
_llama_cpp_busy: bool = False
_busy_since: float | None = None

_byo_gpu_endpoint: str = ""
_byo_gpu_api_key: str = ""
_last_byo_gpu_request: float = 0.0


# ---------------------------------------------------------------------------
# Internal helpers (must be called with _lock held)
# ---------------------------------------------------------------------------

def _do_auto_revert_locked() -> None:
    """Check and apply auto-revert while _lock is already held."""
    global _active_provider, _byo_gpu_endpoint, _byo_gpu_api_key, _last_byo_gpu_request
    if _active_provider != "byo_gpu":
        return
    if _last_byo_gpu_request <= 0:
        return
    elapsed = time.time() - _last_byo_gpu_request
    if elapsed >= settings.byo_gpu_inactivity_secs:
        _active_provider = "llama_cpp"
        _byo_gpu_endpoint = ""
        _byo_gpu_api_key = ""
        _last_byo_gpu_request = 0.0


# ---------------------------------------------------------------------------
# Public read API
# ---------------------------------------------------------------------------

def get_active_provider() -> str:
    """Return the currently active provider name."""
    with _lock:
        return _active_provider


def is_llama_cpp_busy() -> bool:
    """Return True if llama-cpp is currently processing a request."""
    with _lock:
        return _llama_cpp_busy


def get_byo_gpu_settings() -> tuple[str, str]:
    """Return (endpoint, api_key) for the BYO GPU provider."""
    with _lock:
        return _byo_gpu_endpoint, _byo_gpu_api_key


def get_effective_provider_config() -> tuple[str, str, str]:
    """Atomically apply auto-revert and return (provider, endpoint, api_key).

    Use this in create_client() so the check + credential retrieval happen
    in a single lock acquisition (no TOCTOU race between check and read).
    """
    global _active_provider, _byo_gpu_endpoint, _byo_gpu_api_key, _last_byo_gpu_request
    with _lock:
        _do_auto_revert_locked()
        return _active_provider, _byo_gpu_endpoint, _byo_gpu_api_key


def get_status() -> dict:
    """Return a status snapshot suitable for the /provider-status endpoint."""
    with _lock:
        _do_auto_revert_locked()
        now = time.time()
        busy_since_secs: float | None = None
        if _llama_cpp_busy and _busy_since is not None:
            busy_since_secs = round(now - _busy_since, 1)

        auto_revert_in: float | None = None
        if _active_provider == "byo_gpu" and _last_byo_gpu_request > 0:
            elapsed = now - _last_byo_gpu_request
            remaining = settings.byo_gpu_inactivity_secs - elapsed
            auto_revert_in = max(0.0, round(remaining, 1))

        return {
            "active_provider": _active_provider,
            "busy": _llama_cpp_busy,
            "busy_since_secs": busy_since_secs,
            "byo_gpu_configured": bool(_byo_gpu_endpoint),
            "byo_gpu_endpoint_hint": (
                _byo_gpu_endpoint[:30] + "..." if len(_byo_gpu_endpoint) > 30 else _byo_gpu_endpoint
            ) if _byo_gpu_endpoint else "",
            "auto_revert_in_secs": auto_revert_in,
        }


# ---------------------------------------------------------------------------
# Provider switching
# ---------------------------------------------------------------------------

def activate_byo_gpu(endpoint: str, api_key: str) -> None:
    """Switch to BYO GPU provider.  Stores credentials in memory."""
    global _active_provider, _byo_gpu_endpoint, _byo_gpu_api_key, _last_byo_gpu_request
    with _lock:
        _byo_gpu_endpoint = endpoint
        _byo_gpu_api_key = api_key
        _active_provider = "byo_gpu"
        _last_byo_gpu_request = time.time()


def revert_to_local() -> None:
    """Revert to llama-cpp local provider and clear BYO GPU credentials."""
    global _active_provider, _byo_gpu_endpoint, _byo_gpu_api_key, _last_byo_gpu_request
    with _lock:
        _active_provider = "llama_cpp"
        _byo_gpu_endpoint = ""
        _byo_gpu_api_key = ""
        _last_byo_gpu_request = 0.0


def check_auto_revert() -> None:
    """Revert to llama-cpp if BYO GPU has been idle longer than the threshold."""
    with _lock:
        _do_auto_revert_locked()


def record_byo_gpu_request() -> None:
    """Update the last BYO GPU request timestamp to reset the inactivity timer."""
    global _last_byo_gpu_request
    with _lock:
        _last_byo_gpu_request = time.time()


# ---------------------------------------------------------------------------
# llama-cpp busy tracking
# ---------------------------------------------------------------------------

def set_llama_cpp_busy(busy: bool) -> None:
    """Mark llama-cpp as busy (True) or idle (False)."""
    global _llama_cpp_busy, _busy_since
    with _lock:
        _llama_cpp_busy = busy
        _busy_since = time.time() if busy else None
