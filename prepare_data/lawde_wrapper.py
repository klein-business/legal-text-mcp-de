# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Incremental lawde driver with per-law content-hash caching.

The wrapper does NOT shell out to lawde itself. It accepts two callables
(head_fn for cheap upstream-hash probes, fetch_fn for full-body downloads)
so the wider pipeline can compose any combination of real-network and
fixture-driven sources behind a stable interface.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable


@dataclass
class FetchResult:
    """Summary of one update pass."""

    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[tuple[str, str]] = field(default_factory=list)  # (law_id, reason)


@dataclass
class LawdeIncremental:
    """Drives an incremental refresh, skipping content-unchanged laws.

    Parameters
    ----------
    cache_dir
        Directory holding ``<law_id>.sha256`` files (cached upstream hashes)
        and ``<law_id>.bin`` files (last-known payload bytes). Created if needed.
    head_fn
        ``(law_id) -> str`` returning the upstream content hash. Treat exceptions
        as transient — the law is logged in :attr:`FetchResult.failed`.
    fetch_fn
        ``(law_id) -> bytes`` returning the full payload. Called only when the
        upstream hash differs from the cache. Exceptions are recorded as above.
    """

    cache_dir: Path
    head_fn: Callable[[str], str]
    fetch_fn: Callable[[str], bytes]

    def __post_init__(self) -> None:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _cached_hash(self, law_id: str) -> str | None:
        f = self.cache_dir / f"{law_id}.sha256"
        if not f.exists():
            return None
        return f.read_text(encoding="utf-8").strip() or None

    def _store(self, law_id: str, body: bytes) -> None:
        digest = hashlib.sha256(body).hexdigest()
        (self.cache_dir / f"{law_id}.sha256").write_text(digest + "\n", encoding="utf-8")
        (self.cache_dir / f"{law_id}.bin").write_bytes(body)

    def update(self, law_ids: list[str]) -> FetchResult:
        """Probe each law_id, fetch the changed ones, return a summary."""
        out = FetchResult()
        for law_id in law_ids:
            try:
                upstream = self.head_fn(law_id)
            except Exception as exc:
                out.failed.append((law_id, f"head failed: {exc}"))
                continue
            if upstream == self._cached_hash(law_id):
                out.skipped.append(law_id)
                continue
            try:
                body = self.fetch_fn(law_id)
            except Exception as exc:
                out.failed.append((law_id, f"fetch failed: {exc}"))
                continue
            self._store(law_id, body)
            out.updated.append(law_id)
        return out
