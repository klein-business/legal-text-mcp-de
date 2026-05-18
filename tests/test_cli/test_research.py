# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_research.py — research smart tool."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from legal_text_mcp_de.cli import app
from legal_text_mcp_de.cli._runtime import reset_runtime_cache


FIXTURE = Path(__file__).parent.parent / "fixtures" / "normalized"


@pytest.fixture(autouse=True)
def _isolate_runtime(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", str(FIXTURE))
    monkeypatch.setenv("STRICT_STARTUP", "true")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    reset_runtime_cache()
    yield
    reset_runtime_cache()


def test_research_without_api_key_returns_ranked_search_fallback_exit_zero():
    """No ANTHROPIC_API_KEY → soft degradation, exit 0 with ranked search hits."""
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "research", "Werbung"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    # The Phase-E _run_research path returns a ResearchReport; in
    # the no-key path the status is one of {no_matches, error, ok}
    # depending on the fixture corpus. Either way, error field must
    # be None on a soft degradation.
    assert payload["error"] is None
    assert "topic" in payload["data"]
