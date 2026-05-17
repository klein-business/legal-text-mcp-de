# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Hessen (rv.hessenrecht.hessen.de, RV CMS) state-law scraper."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable

from bs4 import BeautifulSoup

from prepare_data.state_law.base import (
    NormalizedLaw,
    NormalizedNorm,
    StateLawRaw,
    StateLawSummary,
)


INDEX_URL = "https://www.rv.hessenrecht.hessen.de/bshe/list?bla=BgRecht"
LAW_URL_TPL = "https://www.rv.hessenrecht.hessen.de/bshe/document/{law_id}/jlr-{law_id}rahmen"
_ABBREV_RE = re.compile(r"\(([^)]+)\)\s*$")


def _default_http_get(url: str) -> str:
    """Real-network default; tests should always inject a fake."""
    import urllib.request

    with urllib.request.urlopen(url, timeout=30) as resp:
        return str(resp.read().decode("utf-8", errors="replace"))


@dataclass
class HEStateLaw:
    """Scraper for rv.hessenrecht.hessen.de (RV CMS).

    `http_get` is injected for testing; in production it defaults to a
    direct urllib call with a 30-second timeout.
    """

    state_code: str = "he"
    http_get: Callable[[str], str] = field(default=_default_http_get)

    def fetch_index(self) -> list[StateLawSummary]:
        body = self.http_get(INDEX_URL)
        soup = BeautifulSoup(body, "html.parser")
        out: list[StateLawSummary] = []
        for a in soup.select("ul.rechtsliste li a"):
            title = a.get_text(strip=True)
            href = str(a.get("href", ""))
            if not title or not href:
                continue
            m = _ABBREV_RE.search(title)
            if not m:
                continue  # need the bracketed abbreviation as law_id
            law_id = m.group(1).strip()
            out.append(StateLawSummary(law_id=law_id, title=title, url=href))
        return out

    def fetch_law(self, law_id: str) -> StateLawRaw:
        url = LAW_URL_TPL.format(law_id=law_id)
        body = self.http_get(url)
        return StateLawRaw(law_id=law_id, body_html=body)

    def normalize(self, raw: StateLawRaw) -> NormalizedLaw:
        soup = BeautifulSoup(raw.body_html, "html.parser")
        h1 = soup.find("h1")
        display_name = h1.get_text(strip=True) if h1 else raw.law_id
        display_code = raw.law_id
        norm_list: list[NormalizedNorm] = []
        for i, div in enumerate(soup.find_all("div", class_="rv-norm")):
            norm_id = str(div.get("id", "")) or f"par-unknown-{i}"
            h3 = div.find("h3")
            title_full = h3.get_text(strip=True) if h3 else ""
            # "§ N Title" → split off the prefix ("§" and "N")
            parts = title_full.split(" ", 2)
            clean_title = parts[2] if len(parts) >= 3 else title_full
            text = " ".join(p.get_text(strip=True) for p in div.find_all("p", class_="rv-text"))
            norm_list.append(NormalizedNorm(norm_id=norm_id, title=clean_title, text=text))
        canonical_slug = display_code.lower().replace(" ", "_")
        return NormalizedLaw(
            canonical_id=f"he/{canonical_slug}",
            display_code=display_code,
            display_name=display_name,
            state_code="he",
            source_url=LAW_URL_TPL.format(law_id=raw.law_id),
            norms=tuple(norm_list),
        )
