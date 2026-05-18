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


def test_cite_resolves_egbgb_art_246a_par_1():
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "--json",
            "cite",
            "--code",
            "EGBGB",
            "--unit",
            "art",
            "--paragraph",
            "246a",
            "--child-unit",
            "par",
            "--child-value",
            "1",
        ],
    )
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["norm"]["canonical_id"] == "egbgb/art:246a/par:1"


def test_search_with_code_filter():
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "search", "Werbung", "--code", "UWG"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["codes"] == ["uwg_2004"]
    assert payload["data"]["results"]


def test_meta_for_dsgvo_includes_eur_lex_kind():
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "meta", "DSGVO"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload["data"]["sources"][0]["source"]["source_kind"] == "eur-lex-cellar"


def test_coverage_returns_counts():
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "coverage"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "generated_package_present" in payload["data"]


def test_limitations_returns_count_field():
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "limitations"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "count" in payload["data"]


def test_related_returns_count_field_zero_or_more():
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "related", "BGB", "§ 355"])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert "count" in payload["data"]


def test_law_missing_dataset_path_raises_runtime_error(monkeypatch):
    """When DATASET_PATH is unset, every lookup exits 1 with structured error."""
    # The autouse fixture sets DATASET_PATH; override with delenv
    monkeypatch.delenv("DATASET_PATH", raising=False)
    reset_runtime_cache()
    runner = CliRunner()
    result = runner.invoke(app, ["--json", "law", "BGB"])
    assert result.exit_code == 1
    payload = json.loads(result.stdout)
    assert payload["error"] is not None
    assert payload["data"] is None


# --------------------------------------------------------------------------
# Parameterised cross-command tests
# --------------------------------------------------------------------------
#
# Each of the nine read-only lookup commands shares the same error envelope.
# Rather than asserting that contract per command (nine near-identical tests),
# parameterise across all nine to lock in:
#
#   1. exit_code == 1 on LegalTextError (DATASET_PATH unset → runtime fails
#      to load fixture corpus)
#   2. JSON envelope `{"data": null, "error": {...}}` is honoured
#   3. The render_error path in cli/_lookups.py is exercised for every
#      command (lifts module coverage from ~77% to ~95%)
#
# The autouse `_isolate_runtime` fixture sets DATASET_PATH; the
# `monkeypatch.delenv` call inside the test overrides it back to unset.

_LOOKUP_ARGVS: list[list[str]] = [
    ["laws"],
    ["law", "BGB"],
    ["norm", "BGB", "§ 355"],
    [
        "cite",
        "--code",
        "BGB",
        "--unit",
        "par",
        "--paragraph",
        "5",
    ],
    ["search", "Werbung"],
    ["meta", "DSGVO"],
    ["coverage"],
    ["limitations"],
    ["related", "BGB", "§ 355"],
]


@pytest.mark.parametrize(
    "argv",
    _LOOKUP_ARGVS,
    ids=[a[0] for a in _LOOKUP_ARGVS],
)
def test_every_lookup_exits_one_on_missing_dataset_path(argv, monkeypatch):
    """Every lookup must surface a structured error envelope (exit 1) when
    the runtime cannot be loaded (DATASET_PATH unset → LegalTextError)."""
    monkeypatch.delenv("DATASET_PATH", raising=False)
    reset_runtime_cache()
    runner = CliRunner()
    result = runner.invoke(app, ["--json", *argv])
    assert result.exit_code == 1, f"argv={argv!r} expected exit 1, got {result.exit_code}\nstdout={result.stdout!r}"
    payload = json.loads(result.stdout)
    assert payload["error"] is not None, f"argv={argv!r} missing error envelope"
    assert payload["data"] is None, f"argv={argv!r} data should be null on error"
    # Error envelope shape — mirrors http_models.ErrorEnvelope
    assert "code" in payload["error"]
    assert "message" in payload["error"]
