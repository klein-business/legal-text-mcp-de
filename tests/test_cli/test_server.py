# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_server.py — flag parsing and port resolution; run is mocked."""

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


def test_http_uses_settings_port_when_no_flag(monkeypatch):
    """Regression: `http` must honour settings.port (PORT env), not hard-code 8080."""
    from legal_text_mcp_de.cli._server import _run_http
    from legal_text_mcp_de.config import settings

    captured = {}

    def fake_uvicorn_run(app_path, *, host, port, log_level):
        captured["port"] = port

    monkeypatch.setattr("uvicorn.run", fake_uvicorn_run)
    monkeypatch.setattr(settings, "port", 12345)

    _run_http(host=None, port=None, dataset=None)

    assert captured["port"] == 12345


def test_http_explicit_port_overrides_settings(monkeypatch):
    """An explicit --port still wins over settings.port."""
    from legal_text_mcp_de.cli._server import _run_http
    from legal_text_mcp_de.config import settings

    captured = {}

    def fake_uvicorn_run(app_path, *, host, port, log_level):
        captured["port"] = port

    monkeypatch.setattr("uvicorn.run", fake_uvicorn_run)
    monkeypatch.setattr(settings, "port", 12345)

    _run_http(host=None, port=9999, dataset=None)

    assert captured["port"] == 9999
