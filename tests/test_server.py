# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for server.py — the FastMCP app factory."""

from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.server import create_mcp_app


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"


def test_mcp_app_serves_health():
    """The MCP streamable-HTTP transport must answer GET /health.

    The Dockerfile HEALTHCHECK probes :8001/health and the default CMD is
    `serve`; without this route every serve-mode container is unhealthy.
    """
    dataset = NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True)
    runtime = LegalTextRuntime.from_dataset(dataset)
    client = TestClient(create_mcp_app(runtime).streamable_http_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
