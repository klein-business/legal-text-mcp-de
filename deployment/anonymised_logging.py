# deployment/anonymised_logging.py
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Logs only method, path, status, latency, tool-name — never request bodies."""

from __future__ import annotations

import json
import logging
import time

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


logger = logging.getLogger("legal_text_mcp_de.hosted")


class AnonymisedLoggingMiddleware(BaseHTTPMiddleware):
    """Per-request structured log line with no PII / no body content.

    Logged fields: method, path, status, latency_ms, ua_hash.
    """

    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        latency_ms = int((time.perf_counter() - start) * 1000)
        ua = request.headers.get("user-agent", "-")
        ua_hash = abs(hash(ua)) % 10000  # cheap UA bucket, no PII retained
        line = json.dumps(
            {
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "latency_ms": latency_ms,
                "ua_bucket": ua_hash,
            }
        )
        logger.info(line)
        return response
