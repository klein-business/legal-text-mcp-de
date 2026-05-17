# deployment/metrics.py
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Prometheus metrics for the hosted MCP service.

Exposes: requests_total{tool, status}, request_latency_seconds histogram,
corpus_version (gauge), rate_limit_rejections_total.
"""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest


REQUESTS_TOTAL = Counter(
    "legal_mcp_requests_total",
    "Total MCP requests served",
    ["tool", "status"],
)

REQUEST_LATENCY = Histogram(
    "legal_mcp_request_latency_seconds",
    "MCP request latency in seconds",
    ["tool"],
)

RATE_LIMIT_REJECTIONS = Counter(
    "legal_mcp_rate_limit_rejections_total",
    "Number of requests rejected by rate-limit middleware",
    ["bucket"],  # "per_minute" or "per_day"
)

CORPUS_VERSION = Gauge(
    "legal_mcp_corpus_version_info",
    "Corpus version currently loaded (always 1; label carries the version string)",
    ["version"],
)


def render_metrics() -> bytes:
    return generate_latest()
