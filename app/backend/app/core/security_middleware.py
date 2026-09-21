# Ref: BL-QA-003 / F8 | Skill: K-007 | Fase: F8
"""Security headers + login rate limit middleware."""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """OWASP-oriented response headers for local API."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-XSS-Protection"] = "0"
        # CSP minimal for API JSON; UI served separately
        if not request.url.path.startswith("/ui"):
            response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
        return response


class LoginRateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limit for /auth/login (local lab)."""

    def __init__(
        self,
        app,
        *,
        max_attempts: int = 10,
        window_seconds: int = 60,
    ) -> None:
        super().__init__(app)
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        from app.core.config import get_settings

        if get_settings().app_env == "test":
            return await call_next(request)
        path = request.url.path
        if request.method == "POST" and path.endswith("/auth/login"):
            client = request.client.host if request.client else "unknown"
            key = f"{client}:{path}"
            now = time.time()
            window = [t for t in self._hits[key] if now - t < self.window_seconds]
            if len(window) >= self.max_attempts:
                return JSONResponse(
                    status_code=429,
                    content={
                        "detail": {
                            "decision": "DENY",
                            "reason_code": "RATE_LIMITED",
                        }
                    },
                )
            window.append(now)
            self._hits[key] = window
        return await call_next(request)
