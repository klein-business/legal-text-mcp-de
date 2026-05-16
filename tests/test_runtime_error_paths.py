# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Cover the error and startup paths of LegalTextRuntime.

These tests lift runtime.py from 79% to 100% statement coverage by
exercising the strict/non-strict bootstrap, the readiness gate, and
the require_dataset/search-laws guards when the dataset is missing.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from legal_text_mcp_de.legal_texts.errors import LegalTextError
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime


@dataclass
class _Settings:
    dataset_path: str | None
    strict_startup: bool


# ---------- from_settings error paths ----------


def test_from_settings_strict_raises_when_dataset_path_missing() -> None:
    settings = _Settings(dataset_path=None, strict_startup=True)
    with pytest.raises(LegalTextError) as exc_info:
        LegalTextRuntime.from_settings(settings)
    assert "DATASET_PATH" in str(exc_info.value)


def test_from_settings_non_strict_returns_runtime_with_startup_error() -> None:
    settings = _Settings(dataset_path=None, strict_startup=False)
    runtime = LegalTextRuntime.from_settings(settings)
    assert runtime.dataset is None
    assert runtime.search is None
    assert runtime.dataset_path is None
    assert runtime.startup_error is not None
    assert "DATASET_PATH" in str(runtime.startup_error)


def test_from_settings_strict_raises_when_dataset_load_fails(tmp_path: object) -> None:
    # tmp_path doesn't contain a valid normalized dataset -> NormalizedDataset.load fails.
    settings = _Settings(dataset_path=str(tmp_path), strict_startup=True)
    with pytest.raises(LegalTextError):
        LegalTextRuntime.from_settings(settings)


def test_from_settings_non_strict_captures_dataset_load_failure(tmp_path: object) -> None:
    settings = _Settings(dataset_path=str(tmp_path), strict_startup=False)
    runtime = LegalTextRuntime.from_settings(settings)
    assert runtime.dataset is None
    assert runtime.search is None
    assert runtime.dataset_path is not None
    assert runtime.startup_error is not None


def test_from_settings_strict_override_with_strict_kwarg(tmp_path: object) -> None:
    """The explicit `strict=False` kwarg wins over settings.strict_startup=True."""

    settings = _Settings(dataset_path=None, strict_startup=True)
    runtime = LegalTextRuntime.from_settings(settings, strict=False)
    assert runtime.startup_error is not None  # captured, not raised


# ---------- readiness / require_dataset / search_laws guards ----------


def _broken_runtime() -> LegalTextRuntime:
    """A runtime where startup_error is set."""

    settings = _Settings(dataset_path=None, strict_startup=False)
    return LegalTextRuntime.from_settings(settings)


def _empty_runtime_no_startup_error() -> LegalTextRuntime:
    """A runtime with no dataset AND no startup_error (paranoia path)."""

    from legal_text_mcp_de.legal_texts.registry import LawRegistry

    return LegalTextRuntime(
        dataset_path=None,
        registry=LawRegistry.load(),
        dataset=None,
        search=None,
        startup_error=None,
    )


def test_readiness_raises_startup_error_when_present() -> None:
    runtime = _broken_runtime()
    with pytest.raises(LegalTextError):
        runtime.readiness()


def test_readiness_raises_dataset_not_ready_when_no_error_no_dataset() -> None:
    runtime = _empty_runtime_no_startup_error()
    with pytest.raises(LegalTextError):
        runtime.readiness()


def test_require_dataset_raises_startup_error_when_present() -> None:
    runtime = _broken_runtime()
    with pytest.raises(LegalTextError):
        runtime.require_dataset()


def test_require_dataset_raises_dataset_not_ready_when_no_error_no_dataset() -> None:
    runtime = _empty_runtime_no_startup_error()
    with pytest.raises(LegalTextError):
        runtime.require_dataset()


def test_search_laws_raises_startup_error_when_present() -> None:
    runtime = _broken_runtime()
    with pytest.raises(LegalTextError):
        runtime.search_laws("test")


def test_search_laws_raises_dataset_not_ready_when_search_missing() -> None:
    runtime = _empty_runtime_no_startup_error()
    with pytest.raises(LegalTextError):
        runtime.search_laws("test")
