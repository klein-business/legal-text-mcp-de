# deployment/health.py
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Extended /health: returns corpus version + uptime + dataset state."""

from __future__ import annotations

import time
from typing import Any


_STARTED_AT = time.time()


def health_payload(*, corpus_version: str | None = None, dataset_ready: bool = True) -> dict[str, Any]:
    return {
        "status": "ok" if dataset_ready else "degraded",
        "uptime_s": int(time.time() - _STARTED_AT),
        "corpus_version": corpus_version or "unknown",
    }
