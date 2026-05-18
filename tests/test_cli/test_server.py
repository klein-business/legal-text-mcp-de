# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_server.py — flag parsing only, mcp.run() is mocked."""

from __future__ import annotations

from typer.testing import CliRunner

from legal_text_mcp_de.cli import app


def test_serve_runs_mcp_app(monkeypatch):
    invoked = {}

    def fake_run(transport: str) -> None:
        invoked["transport"] = transport

    # Patch the create_mcp_app().run reference used by serve
    import legal_text_mcp_de.cli._server as srv_mod

    monkeypatch.setattr(srv_mod, "_run_mcp", lambda **kw: invoked.update(kw))

    runner = CliRunner()
    result = runner.invoke(app, ["serve", "--host", "127.0.0.1", "--port", "9999"])
    assert result.exit_code == 0
    assert invoked.get("host") == "127.0.0.1"
    assert invoked.get("port") == 9999
