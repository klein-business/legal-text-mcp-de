# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_diagnostic.py — health, version, completion."""

from __future__ import annotations

import httpx
from typer.testing import CliRunner

from legal_text_mcp_de.cli import app


def test_version_subcommand_prints_2_x():
    runner = CliRunner()
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "2." in result.stdout


def test_health_returns_zero_when_endpoint_ok(monkeypatch):
    def fake_get(url, timeout=None):
        return httpx.Response(200, json={"status": "ok"})

    import legal_text_mcp_de.cli._diagnostic as dmod

    monkeypatch.setattr(dmod.httpx, "get", fake_get)

    runner = CliRunner()
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 0


def test_health_returns_five_when_endpoint_unreachable(monkeypatch):
    def fake_get(url, timeout=None):
        raise httpx.ConnectError("connection refused")

    import legal_text_mcp_de.cli._diagnostic as dmod

    monkeypatch.setattr(dmod.httpx, "get", fake_get)

    runner = CliRunner()
    result = runner.invoke(app, ["health"])
    assert result.exit_code == 5


def test_completion_show_bash_prints_to_stdout():
    runner = CliRunner()
    result = runner.invoke(app, ["completion", "show", "bash"])
    assert result.exit_code == 0
    assert "_LEGAL_TEXT_MCP_DE_COMPLETE" in result.stdout or "complete" in result.stdout.lower()
