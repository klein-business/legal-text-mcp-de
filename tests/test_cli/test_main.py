# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Smoke tests for the CLI root app."""

from __future__ import annotations

from typer.testing import CliRunner

from legal_text_mcp_de.cli import app


def test_bare_invocation_prints_help_and_exits_zero():
    runner = CliRunner()
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "Usage:" in result.stdout


def test_unknown_subcommand_exits_two():
    runner = CliRunner()
    result = runner.invoke(app, ["bogus-command"])
    assert result.exit_code == 2


def test_version_flag_prints_version_and_exits_zero():
    runner = CliRunner()
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "2." in result.stdout  # any 2.x version
