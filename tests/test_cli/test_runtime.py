# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_runtime.py — lazy LegalTextRuntime loader."""

from __future__ import annotations

from pathlib import Path

import pytest

from legal_text_mcp_de.cli._runtime import get_runtime_or_die
from legal_text_mcp_de.legal_texts.errors import LegalTextError


FIXTURE = Path(__file__).parent.parent / "fixtures" / "normalized"


def test_get_runtime_or_die_with_valid_dataset(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", str(FIXTURE))
    monkeypatch.setenv("STRICT_STARTUP", "true")
    runtime = get_runtime_or_die()
    assert runtime is not None
    assert runtime.dataset is not None


def test_get_runtime_or_die_caches_between_calls(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", str(FIXTURE))
    monkeypatch.setenv("STRICT_STARTUP", "true")
    r1 = get_runtime_or_die()
    r2 = get_runtime_or_die()
    assert r1 is r2


def test_get_runtime_or_die_raises_on_missing_dataset(monkeypatch):
    monkeypatch.delenv("DATASET_PATH", raising=False)
    monkeypatch.setenv("STRICT_STARTUP", "true")
    # Force cache clear
    from legal_text_mcp_de.cli import _runtime

    _runtime._cached_runtime = None
    with pytest.raises(LegalTextError):
        get_runtime_or_die()
