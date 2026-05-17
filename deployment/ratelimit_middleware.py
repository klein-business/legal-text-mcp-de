# deployment/ratelimit_middleware.py
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Per-IP / per-token rate-limit middleware for the hosted MCP service."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket rate limit per (ip, token) tuple.

    Defaults: 100 req/min/IP + 1000 req/day/IP. Caller IDs are the
    bearer token if present, otherwise the source IP.
    """

    def __init__(
        self,
        app,
        per_minute: int = 100,
        per_day: int = 1000,
    ) -> None:
        super().__init__(app)
        self.per_minute = per_minute
        self.per_day = per_day
        self._minute_buckets: dict[str, deque[float]] = defaultdict(deque)
        self._day_buckets: dict[str, deque[float]] = defaultdict(deque)

    def _key(self, request: Request) -> str:
        auth = request.headers.get("authorization", "")
        if auth.lower().startswith("bearer "):
            return f"token:{auth[7:][:32]}"
        client = request.client.host if request.client else "unknown"
        return f"ip:{client}"

    async def dispatch(self, request: Request, call_next):
        now = time.time()
        key = self._key(request)
        # Prune old timestamps
        minute_bucket = self._minute_buckets[key]
        while minute_bucket and minute_bucket[0] < now - 60:
            minute_bucket.popleft()
        day_bucket = self._day_buckets[key]
        while day_bucket and day_bucket[0] < now - 86400:
            day_bucket.popleft()
        if len(minute_bucket) >= self.per_minute:
            return JSONResponse(
                {"error": "rate limit exceeded (per-minute)"},
                status_code=429,
                headers={"Retry-After": "60"},
            )
        if len(day_bucket) >= self.per_day:
            return JSONResponse(
                {"error": "rate limit exceeded (per-day)"},
                status_code=429,
                headers={"Retry-After": "86400"},
            )
        minute_bucket.append(now)
        day_bucket.append(now)
        return await call_next(request)
