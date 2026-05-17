# deployment/bearer_token.py
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Optional bearer-token validation for the hosted service.

The hosted service supports two modes:
1. Open with per-IP rate limit (no auth required)
2. Bearer-token gated (higher per-token quotas)

This module provides a callable that returns the resolved caller-id or None.
"""

from __future__ import annotations

import os


def _allowed_tokens() -> set[str]:
    """Read allowed bearer tokens from env HOSTED_BEARER_TOKENS (comma-separated)."""
    raw = os.environ.get("HOSTED_BEARER_TOKENS", "")
    return {t.strip() for t in raw.split(",") if t.strip()}


def validate_bearer(authorization_header: str | None) -> str | None:
    """Return the token if valid (and present in env), otherwise None.

    Falsy return = use IP-based limits. Valid return = use per-token limits.
    """
    if not authorization_header:
        return None
    parts = authorization_header.split(" ", 1)
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    token = parts[1].strip()
    if not token or token not in _allowed_tokens():
        return None
    return token
