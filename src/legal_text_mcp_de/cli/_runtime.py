# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Lazy LegalTextRuntime loader for the CLI.

Each CLI subcommand resolves the runtime through `get_runtime_or_die()`
so that env-var changes (DATASET_PATH, STRICT_STARTUP) take effect on
every fresh process invocation. The runtime is cached per-process so
that multi-subcommand sessions (e.g. piped invocations) don't re-load
the dataset.
"""

from __future__ import annotations

from legal_text_mcp_de.config import Settings
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime


_cached_runtime: LegalTextRuntime | None = None


def get_runtime_or_die() -> LegalTextRuntime:
    """Return a ready LegalTextRuntime; raise LegalTextError otherwise."""
    global _cached_runtime
    if _cached_runtime is not None:
        return _cached_runtime
    settings = Settings()  # picks up env vars at call time
    runtime = LegalTextRuntime.from_settings(settings, strict=True)
    _cached_runtime = runtime
    return runtime


def reset_runtime_cache() -> None:
    """Test helper: clear the per-process runtime cache."""
    global _cached_runtime
    _cached_runtime = None
