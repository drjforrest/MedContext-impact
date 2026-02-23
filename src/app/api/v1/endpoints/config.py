"""Runtime provider configuration endpoints.

Allows the admin to switch between the local llama-cpp provider and a BYO GPU
endpoint at runtime without restarting the server.  All mutating endpoints
require the request to originate from the configured ADMIN_IP.
"""

from __future__ import annotations

import ipaddress
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.core import provider_state

router = APIRouter()


# Private/loopback CIDR ranges that must not be reachable via BYO GPU endpoint
_PRIVATE_NETWORKS = [
    ipaddress.ip_network("127.0.0.0/8"),    # Loopback
    ipaddress.ip_network("10.0.0.0/8"),     # RFC1918
    ipaddress.ip_network("172.16.0.0/12"),  # RFC1918
    ipaddress.ip_network("192.168.0.0/16"), # RFC1918
    ipaddress.ip_network("169.254.0.0/16"), # Link-local / AWS metadata
    ipaddress.ip_network("::1/128"),        # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),       # IPv6 private
]


def _validate_byo_endpoint(endpoint: str) -> None:
    """Raise HTTPException if the endpoint URL looks like an SSRF target."""
    try:
        parsed = urlparse(endpoint)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid endpoint URL.")

    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=422,
            detail="Endpoint must use http:// or https:// scheme.",
        )

    hostname = parsed.hostname or ""
    # Reject bare IP addresses that are in private ranges
    try:
        addr = ipaddress.ip_address(hostname)
        for net in _PRIVATE_NETWORKS:
            if addr in net:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        "Endpoint must not point to a private or loopback address. "
                        "Use a publicly reachable GPU server URL."
                    ),
                )
    except ValueError:
        # Not an IP literal — reject well-known localhost hostnames
        if hostname in ("localhost", "localhost.localdomain"):
            raise HTTPException(
                status_code=422,
                detail="Endpoint must not use 'localhost'. Use a publicly reachable URL.",
            )


def _require_admin(request: Request) -> None:
    """Raise 403 unless the request comes from the admin IP.

    Uses ONLY the direct TCP connection IP (request.client.host), NOT
    X-Forwarded-For, to prevent header spoofing by untrusted clients.
    """
    if not settings.admin_ip:
        # No admin IP configured — allow (development / local-only mode)
        return
    direct_ip = request.client.host if request.client else "unknown"
    if direct_ip != settings.admin_ip:
        raise HTTPException(
            status_code=403,
            detail=(
                "This action requires admin access. "
                "Configure ADMIN_IP on the server to enable remote management."
            ),
        )


# ---------------------------------------------------------------------------
# Read endpoints (public — no admin required)
# ---------------------------------------------------------------------------

@router.get("/provider-status")
def get_provider_status() -> dict:
    """Return the current provider status, busy state, and BYO GPU info."""
    return provider_state.get_status()


# ---------------------------------------------------------------------------
# Write endpoints (admin-only)
# ---------------------------------------------------------------------------

class BYOGPURequest(BaseModel):
    endpoint: str
    api_key: str = ""


@router.post("/activate-byo-gpu")
def activate_byo_gpu(body: BYOGPURequest, request: Request) -> dict:
    """Switch to a user-provided GPU endpoint for MedGemma inference.

    Requires the request to originate from ADMIN_IP.
    The active provider will automatically revert to llama-cpp after
    BYO_GPU_INACTIVITY_SECS seconds of inactivity.
    """
    _require_admin(request)

    if not body.endpoint.strip():
        raise HTTPException(status_code=422, detail="endpoint must not be empty")

    _validate_byo_endpoint(body.endpoint.strip())

    provider_state.activate_byo_gpu(
        endpoint=body.endpoint.strip(),
        api_key=body.api_key.strip(),
    )
    return {
        "status": "ok",
        "active_provider": "byo_gpu",
        "auto_revert_after_secs": settings.byo_gpu_inactivity_secs,
        "message": (
            f"BYO GPU activated. Will auto-revert to llama-cpp after "
            f"{settings.byo_gpu_inactivity_secs}s of inactivity."
        ),
    }


@router.post("/revert-to-local")
def revert_to_local(request: Request) -> dict:
    """Immediately revert to the local llama-cpp provider.

    Requires the request to originate from ADMIN_IP.
    """
    _require_admin(request)
    provider_state.revert_to_local()
    return {
        "status": "ok",
        "active_provider": "llama_cpp",
        "message": "Reverted to local llama-cpp provider.",
    }
