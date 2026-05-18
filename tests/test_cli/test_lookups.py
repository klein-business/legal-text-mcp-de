# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_lookups.py — the 9 read-only commands."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from legal_text_mcp_de.cli import app
from legal_text_mcp_de.cli._runtime import reset_runtime_cache
from legal_text_mcp_de.http_models import LawListResponse


FIXTURE = Path(__file__).parent.parent / "fixtures" / "normalized"


@pytest.fixture(autouse=True)
def _isolate_runtime(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", str(FIXTURE))
    monkeypatch.setenv("STRICT_STARTUP", "true")
    reset_runtime_cache()
    yield
    reset_runtime_cache()


def test_laws_text_output_shows_law_count():
    runner = CliRunner()
    result = runner.invoke(app, ["laws"])
    assert result.exit_code == 0
    assert "BGB" in result.stdout or "bgb" in result.stdout


def test_laws_json_output_validates_against_http_schema():
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "laws"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["error"] is None
    LawListResponse.model_validate(payload["data"])  # contract check


def test_laws_with_query_filter():
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "laws", "--query", "DSGVO"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    # DSGVO must appear in at least one canonical_id
    ids = [law["canonical_id"] for law in payload["data"]["laws"]]
    assert any("dsgvo" in cid.lower() for cid in ids)


def test_law_text_output_shows_canonical_id():
    runner = CliRunner()
    result = runner.invoke(app, ["law", "BGB"])
    assert result.exit_code == 0
    assert "BGB" in result.stdout or "bgb" in result.stdout


def test_law_unknown_code_returns_runtime_error_exit_1():
    runner = CliRunner()
    result = runner.invoke(app, ["law", "DOES_NOT_EXIST"])
    assert result.exit_code == 1


def test_norm_returns_norm_payload():
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "norm", "BGB", "§ 355"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["norm"]["canonical_id"] == "bgb/par:355"


def test_norm_unknown_returns_runtime_error_exit_1():
    runner = CliRunner()
    result = runner.invoke(app, ["norm", "BGB", "§ 999999"])
    assert result.exit_code == 1
