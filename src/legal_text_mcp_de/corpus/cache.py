# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""User-level cache for corpus bundles under XDG conventions."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _xdg_cache_home() -> Path:
    base = os.environ.get("XDG_CACHE_HOME") or str(Path.home() / ".cache")
    return Path(base)


def _default_path() -> Path:
    return _xdg_cache_home() / "legal-text-mcp-de"


@dataclass
class CorpusCache:
    """Manages cached corpus bundles in ``$XDG_CACHE_HOME/legal-text-mcp-de/``.

    Layout: one file per cached version, named ``corpus-<version>.tar.zst``.
    """

    path: Path = field(default_factory=_default_path)

    def __post_init__(self) -> None:
        self.path.mkdir(parents=True, exist_ok=True)

    def find_bundle(self, *, version: str) -> Path | None:
        candidate = self.path / f"corpus-{version}.tar.zst"
        return candidate if candidate.exists() else None

    def store_bundle(self, *, version: str, payload: bytes) -> Path:
        target = self.path / f"corpus-{version}.tar.zst"
        target.write_bytes(payload)
        return target
