"""
Security-hardening HTTP response headers and memory guard middlewares.
No third-party package needed; Starlette/FastAPI middleware is enough.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.config import settings

if TYPE_CHECKING:
    from fastapi import Request
    from starlette.responses import Response

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), camera=(), microphone=()"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        # Remove server identity
        if "server" in response.headers:
            del response.headers["server"]
        return response


class MemoryGuardMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        try:
            # Only available on Linux (Render runs Linux)
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("VmRSS:"):
                        kb = int(line.split()[1])
                        mb = kb / 1024
                        if mb > settings.memory_guard_mb:
                            logger.warning("Memory guard tripped: %.1f MB", mb)
                            from fastapi.responses import JSONResponse

                            return JSONResponse(
                                status_code=503,
                                content={
                                    "error": "Server busy",
                                    "code": "SERVER_BUSY",
                                    "detail": "Memory limit reached; try again shortly",
                                },
                            )
        except OSError:
            pass  # /proc not available on Windows dev machine; skip
        return await call_next(request)
