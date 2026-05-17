# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Baden-Württemberg (landesrecht-bw.de, jportal) state-law scraper."""

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


INDEX_URL = "https://www.landesrecht-bw.de/jportal/portal/page/bsbawueprod.psml?nav=lawList"
LAW_URL_TPL = "https://www.landesrecht-bw.de/jportal/portal/t/{law_id}/page/bsbawueprod.psml?showdoccase=1"
_ABBREV_RE = re.compile(r"\(([^)]+)\)\s*$")


def _default_http_get(url: str) -> str:
    """Real-network default; tests should always inject a fake."""
    import urllib.request

    with urllib.request.urlopen(url, timeout=30) as resp:
        return str(resp.read().decode("utf-8", errors="replace"))


@dataclass
class BWStateLaw:
    """Scraper for landesrecht-bw.de (jportal).

    `http_get` is injected for testing; in production it defaults to a
    direct urllib call with a 30-second timeout.
    """

    state_code: str = "bw"
    http_get: Callable[[str], str] = field(default=_default_http_get)

    def fetch_index(self) -> list[StateLawSummary]:
        body = self.http_get(INDEX_URL)
        soup = BeautifulSoup(body, "html.parser")
        out: list[StateLawSummary] = []
        for a in soup.select("ul.law-list li a"):
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
        for i, div in enumerate(soup.find_all("div", class_="jnnorm")):
            norm_id = str(div.get("id", "")) or f"par-unknown-{i}"
            h2 = div.find("h2")
            title_full = h2.get_text(strip=True) if h2 else ""
            # "§ N Title" → split off the prefix
            parts = title_full.split(" ", 2)
            clean_title = parts[2] if len(parts) >= 3 else title_full
            text = " ".join(p.get_text(strip=True) for p in div.find_all("p", class_="jurAbsatz"))
            norm_list.append(NormalizedNorm(norm_id=norm_id, title=clean_title, text=text))
        canonical_slug = display_code.lower().replace(" ", "_")
        return NormalizedLaw(
            canonical_id=f"bw/{canonical_slug}",
            display_code=display_code,
            display_name=display_name,
            state_code="bw",
            source_url=LAW_URL_TPL.format(law_id=raw.law_id),
            norms=tuple(norm_list),
        )
