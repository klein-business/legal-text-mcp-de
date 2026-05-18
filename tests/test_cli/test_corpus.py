# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_corpus.py — corpus pull / verify / info (subprocess mocked)."""

from __future__ import annotations

from typer.testing import CliRunner

from legal_text_mcp_de.cli import app


def test_corpus_pull_invokes_oras_with_version(monkeypatch):
    called = {}

    def fake_run(args, capture_output=False, check=False, **kw):
        called["args"] = args

        class _R:
            returncode = 0
            stdout = b""
            stderr = b""

        return _R()

    import legal_text_mcp_de.cli._corpus as cmod

    monkeypatch.setattr(cmod.subprocess, "run", fake_run)

    runner = CliRunner()
    result = runner.invoke(app, ["corpus", "pull", "--version", "1.5.0"])
    assert result.exit_code == 0
    assert any("1.5.0" in str(part) for part in called["args"])


def test_corpus_verify_invokes_cosign(monkeypatch, tmp_path):
    # Place a fake bundle in the cache dir so `verify` doesn't bail on "no bundle".
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    (tmp_path / "legal-text-mcp-de").mkdir(parents=True, exist_ok=True)
    (tmp_path / "legal-text-mcp-de" / "corpus-1.0.tar.zst").write_bytes(b"fake")

    called = {}

    def fake_run(args, capture_output=False, check=False, **kw):
        called["args"] = args

        class _R:
            returncode = 0
            stdout = b"Verified OK"
            stderr = b""

        return _R()

    import legal_text_mcp_de.cli._corpus as cmod

    monkeypatch.setattr(cmod.subprocess, "run", fake_run)

    runner = CliRunner()
    result = runner.invoke(app, ["corpus", "verify"])
    assert result.exit_code == 0
    assert any("cosign" in str(part) for part in called["args"])


def test_corpus_info_returns_zero_when_cache_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "corpus", "info"])
    assert result.exit_code == 0
