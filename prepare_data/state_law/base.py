# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Common interface for state-law scrapers.

Each Bundesland provides a class that implements StateLawSource. The
downstream normalizer (Task A13) consumes NormalizedLaw objects produced
by these scrapers and folds them into the corpus bundle.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class StateLawSummary:
    """One entry from a Bundesland's law-index page."""

    law_id: str
    title: str
    url: str


@dataclass(frozen=True)
class StateLawRaw:
    """Raw HTML body of one fetched law."""

    law_id: str
    body_html: str


@dataclass(frozen=True)
class NormalizedNorm:
    """One norm (article or paragraph) inside a normalised law."""

    norm_id: str
    title: str
    text: str


@dataclass(frozen=True)
class NormalizedLaw:
    """Normalised representation of one state law, ready for the bundle."""

    canonical_id: str  # e.g. "by/baybo"
    display_code: str  # e.g. "BayBO"
    display_name: str
    state_code: str  # 'by', 'nrw', 'bw', 'nds', 'he'
    source_url: str
    norms: list[NormalizedNorm]


@runtime_checkable
class StateLawSource(Protocol):
    """Contract every Bundesland-specific scraper must satisfy."""

    state_code: str

    def fetch_index(self) -> list[StateLawSummary]: ...
    def fetch_law(self, law_id: str) -> StateLawRaw: ...
    def normalize(self, raw: StateLawRaw) -> NormalizedLaw: ...
