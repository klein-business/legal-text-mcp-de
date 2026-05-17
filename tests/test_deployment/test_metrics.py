# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from deployment.metrics import (
    CORPUS_VERSION,
    RATE_LIMIT_REJECTIONS,
    REQUEST_LATENCY,
    REQUESTS_TOTAL,
    render_metrics,
)


def test_metrics_are_renderable():
    REQUESTS_TOTAL.labels(tool="list_laws", status="200").inc()
    body = render_metrics()
    assert b"legal_mcp_requests_total" in body


def test_corpus_version_gauge_takes_label():
    CORPUS_VERSION.labels(version="2026-05").set(1)
    body = render_metrics()
    assert b"legal_mcp_corpus_version_info" in body
    assert b"2026-05" in body
