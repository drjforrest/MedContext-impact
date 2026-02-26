"""Demo protection middleware - access code validation and rate limiting."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings


class DemoProtectionMiddleware(BaseHTTPMiddleware):
    """Access code validation, rate limiting, and llama-cpp resource protection."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        # In-memory rate limiting (IP -> list of timestamps)
        self._request_log: dict[str, list[float]] = defaultdict(list)
        self._rate_limit_requests = 10  # default requests per hour (cloud/BYO GPU)
        self._rate_limit_window = 3600  # 1 hour in seconds

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP from request."""
        # Check X-Forwarded-For for proxy/load balancer scenarios
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Take first IP in chain
            return forwarded.split(",")[0].strip()
        # Fallback to direct connection
        return request.client.host if request.client else "unknown"

    def _check_rate_limit(self, ip: str, limit: int | None = None) -> bool:
        """Check if IP has exceeded the rate limit.

        Uses ``limit`` if provided, otherwise the default (10/hr).
        Returns False if the limit is exceeded.
        """
        effective_limit = limit if limit is not None else self._rate_limit_requests
        now = time.time()
        cutoff = now - self._rate_limit_window
        self._request_log[ip] = [ts for ts in self._request_log[ip] if ts > cutoff]

        if len(self._request_log[ip]) >= effective_limit:
            return False

        self._request_log[ip].append(now)
        return True

    @staticmethod
    def _is_protected_endpoint(path: str) -> bool:
        """Check if endpoint requires protection."""
        # Protect main API endpoints, but not health check or docs
        protected_prefixes = [
            "/api/v1/orchestrator",
            "/api/v1/ingestion",
            "/api/v1/forensics",
            "/api/v1/reverse-search",
            "/api/v1/analytics",
        ]
        return any(path.startswith(prefix) for prefix in protected_prefixes)

    @staticmethod
    def _validate_access_code(request: Request) -> bool:
        """Validate access code from header or query param."""
        # Skip validation if no demo code is configured (local dev)
        if not settings.demo_access_code:
            return True

        # Check header first
        header_code = request.headers.get("X-Demo-Access-Code", "")
        if header_code == settings.demo_access_code:
            return True

        # Check query parameter
        query_code = request.query_params.get("access_code", "")
        if query_code == settings.demo_access_code:
            return True

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request through protection checks."""
        # Skip protection for non-protected endpoints
        if not self._is_protected_endpoint(request.url.path):
            return await call_next(request)

        # Admin IP bypass — skip all access code and rate limit checks
        client_ip = self._get_client_ip(request)
        if settings.admin_ip and client_ip == settings.admin_ip:
            return await call_next(request)

        # Validate access code
        if not self._validate_access_code(request):
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Access denied. Valid access code required. See README for instructions."
                },
            )

        # Determine rate limit: llama-cpp gets a tighter limit because it is
        # single-threaded — running concurrent requests would queue them for
        # minutes each.  Cloud/BYO GPU endpoints handle their own concurrency.
        from app.core import provider_state as _ps
        if _ps.get_active_provider() == "llama_cpp":
            effective_limit = settings.llama_cpp_rate_limit
            limit_label = f"{effective_limit} requests/hr (local model limit)"
        else:
            effective_limit = self._rate_limit_requests
            limit_label = f"{effective_limit} requests/hr"

        if not self._check_rate_limit(client_ip, limit=effective_limit):
            extra = (
                " The local model processes one request at a time — please wait a few minutes."
                if _ps.get_active_provider() == "llama_cpp" else ""
            )
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Maximum {limit_label}.{extra}"
                },
            )

        # Proceed with request
        return await call_next(request)
