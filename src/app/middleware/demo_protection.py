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
    """Simple access code validation and rate limiting for demo deployments."""

    def __init__(self, app, **kwargs):
        super().__init__(app, **kwargs)
        # In-memory rate limiting (IP -> list of timestamps)
        self._request_log: dict[str, list[float]] = defaultdict(list)
        self._rate_limit_requests = 10  # requests per hour
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

    def _check_rate_limit(self, ip: str) -> bool:
        """Check if IP has exceeded rate limit."""
        now = time.time()
        # Clean old timestamps outside window
        cutoff = now - self._rate_limit_window
        self._request_log[ip] = [ts for ts in self._request_log[ip] if ts > cutoff]

        # Check if over limit
        if len(self._request_log[ip]) >= self._rate_limit_requests:
            return False

        # Log this request
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

        # Validate access code
        if not self._validate_access_code(request):
            return JSONResponse(
                status_code=403,
                content={
                    "detail": "Access denied. Valid access code required. See README for instructions."
                },
            )

        # Check rate limit
        client_ip = self._get_client_ip(request)
        if not self._check_rate_limit(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Maximum {self._rate_limit_requests} requests per hour."
                },
            )

        # Proceed with request
        return await call_next(request)
