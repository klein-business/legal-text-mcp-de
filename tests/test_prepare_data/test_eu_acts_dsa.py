# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from prepare_data.eu_acts.dsa import CELEX, DISPLAY_CODE, DSAAct


FAKE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<DOCUMENT>
  <LG.DOC>DE</LG.DOC>
  <ACT>
    <ARTICLE IDENTIFIER="001">
      <NO.ARTICLE>Artikel 1</NO.ARTICLE>
      <TI.ART>Gegenstand</TI.ART>
      <ALINEA>Diese Verordnung regelt \xe2\x80\xa6</ALINEA>
    </ARTICLE>
  </ACT>
</DOCUMENT>
"""


def test_dsa_resolves_and_normalises():
    fake_url = f"https://eur-lex.europa.eu/legal-content/DE/TXT/XML/?uri=CELEX:{CELEX}"

    def fake_resolve(celex: str, lang: str) -> str:
        assert celex == CELEX
        assert lang == "DE"
        return fake_url

    def fake_http_get(url: str) -> bytes:
        assert url == fake_url
        return FAKE_XML

    act = DSAAct(resolve_xml_url=fake_resolve, http_get=fake_http_get)
    norm = act.fetch_and_normalise()

    assert norm.canonical_id == f"eu/{CELEX.lower()}"
    assert norm.state_code == "eu"
    assert norm.display_code == DISPLAY_CODE
    assert len(norm.norms) >= 1
