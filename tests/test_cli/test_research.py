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


def test_research_sampling_error_returns_exit_three(monkeypatch):
    """When _run_research raises SamplingError, CLI exits 3 with structured error."""
    from legal_text_mcp_de.sampling.errors import SamplingTimeout
    import legal_text_mcp_de.cli._research as rmod

    async def boom(*args, **kwargs):
        raise SamplingTimeout("simulated timeout")

    monkeypatch.setattr(rmod, "_run_research", boom)

    runner = CliRunner()
    result = runner.invoke(app, ["--json", "research", "Werbung"])
    assert result.exit_code == 3
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "SAMPLING_FAILED"
    assert "simulated timeout" in payload["error"]["message"]


def test_research_legal_text_error_returns_exit_one(monkeypatch):
    """When _run_research raises LegalTextError, CLI exits 1."""
    from legal_text_mcp_de.legal_texts.errors import LegalTextError
    import legal_text_mcp_de.cli._research as rmod

    async def boom(*args, **kwargs):
        raise LegalTextError("DATASET_NOT_READY", "dataset missing")

    monkeypatch.setattr(rmod, "_run_research", boom)

    runner = CliRunner()
    result = runner.invoke(app, ["--json", "research", "X"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["error"]["code"] == "DATASET_NOT_READY"
