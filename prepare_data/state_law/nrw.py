# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""NRW (recht.nrw.de) state-law scraper.

Index page lists each law as a row in `table.lawList`. Each row contains
a link with the abbreviation in brackets at the end of the link text
(e.g. `"Bauordnung NRW (BauO NRW)"`). The href is a `br_bes_text?...`
query string identifying the law row.

Because the NRW URL slug is an opaque numeric tuple, the bracketed
abbreviation is used as the law_id everywhere downstream.
"""

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


INDEX_URL = "https://recht.nrw.de/lmi/owa/br_bes_lst"
LAW_URL_TPL = "https://recht.nrw.de/lmi/owa/br_bes_text?{query}"
_ABBREV_RE = re.compile(r"\(([^)]+)\)\s*$")


def _default_http_get(url: str) -> str:
    """Real-network default; tests should always inject a fake."""
    import urllib.request

    with urllib.request.urlopen(url, timeout=30) as resp:
        return str(resp.read().decode("utf-8", errors="replace"))


@dataclass
class NRWStateLaw:
    """Scraper for recht.nrw.de.

    `http_get` is injected for testing; in production it defaults to a
    direct urllib call with a 30-second timeout.
    """

    state_code: str = "nrw"
    http_get: Callable[[str], str] = field(default=_default_http_get)

    def fetch_index(self) -> list[StateLawSummary]:
        body = self.http_get(INDEX_URL)
        soup = BeautifulSoup(body, "html.parser")
        out: list[StateLawSummary] = []
        for a in soup.select("table.lawList tr td a"):
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
        # We don't keep the URL query for each id; reconstruct via search-like URL.
        # In practice the caller stores the StateLawSummary.url; this helper
        # is for ad-hoc lookups by law_id when the index has already been fetched.
        url = LAW_URL_TPL.format(query=f"law_id={law_id}")
        body = self.http_get(url)
        return StateLawRaw(law_id=law_id, body_html=body)

    def normalize(self, raw: StateLawRaw) -> NormalizedLaw:
        soup = BeautifulSoup(raw.body_html, "html.parser")
        h1 = soup.find("h1")
        display_name = h1.get_text(strip=True) if h1 else raw.law_id
        display_code = raw.law_id
        norm_list: list[NormalizedNorm] = []
        for i, div in enumerate(soup.find_all("div", class_="paragraph")):
            norm_id = str(div.get("id", "")) or f"par-unknown-{i}"
            h3 = div.find("h3")
            title_full = h3.get_text(strip=True) if h3 else ""
            # "§ N Title" → split off the prefix
            parts = title_full.split(" ", 2)
            clean_title = parts[2] if len(parts) >= 3 else title_full
            text = " ".join(p.get_text(strip=True) for p in div.find_all("p"))
            norm_list.append(NormalizedNorm(norm_id=norm_id, title=clean_title, text=text))
        canonical_slug = display_code.lower().replace(" ", "_")
        return NormalizedLaw(
            canonical_id=f"nrw/{canonical_slug}",
            display_code=display_code,
            display_name=display_name,
            state_code="nrw",
            source_url=LAW_URL_TPL.format(query=f"law_id={raw.law_id}"),
            norms=tuple(norm_list),
        )
