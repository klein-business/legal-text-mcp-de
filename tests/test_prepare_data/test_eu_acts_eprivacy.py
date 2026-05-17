# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from prepare_data.eu_acts.eprivacy import EPrivacyAct


# Minimal Cellar DOC_2 XML with one article, structured exactly as the real
# EUR-Lex XML uses: ARTICLE with IDENTIFIER attribute, TI.ART for the title,
# and ALINEA for the body text.
FAKE_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<DOCUMENT>
  <LG.DOC>DE</LG.DOC>
  <ACT>
    <ARTICLE IDENTIFIER="001">
      <NO.ARTICLE>Artikel 1</NO.ARTICLE>
      <TI.ART>Geltungsbereich</TI.ART>
      <ALINEA>Diese Richtlinie sieht die Harmonisierung der Vorschriften der Mitgliedstaaten vor.</ALINEA>
    </ARTICLE>
  </ACT>
</DOCUMENT>
"""


def test_eprivacy_resolves_and_normalises():
    fake_url = "https://eur-lex.europa.eu/legal-content/DE/TXT/XML/?uri=CELEX:32002L0058"

    def fake_resolve(celex: str, lang: str) -> str:
        assert celex == "32002L0058"
        assert lang == "DE"
        return fake_url

    def fake_http_get(url: str) -> bytes:
        assert url == fake_url
        return FAKE_XML

    act = EPrivacyAct(resolve_xml_url=fake_resolve, http_get=fake_http_get)
    norm = act.fetch_and_normalise()

    assert norm.canonical_id == "eu/32002l0058"
    assert norm.state_code == "eu"
    assert norm.display_code == "ePrivacy"
    assert len(norm.norms) >= 1
    first = norm.norms[0]
    assert "Harmonisierung" in first.text or "Geltungsbereich" in first.title


def test_eprivacy_norm_id_format():
    """norm_id must follow the art:<number> pattern."""
    fake_url = "https://example.invalid/eprivacy.xml"
    act = EPrivacyAct(
        resolve_xml_url=lambda celex, lang: fake_url,
        http_get=lambda url: FAKE_XML,
    )
    norm = act.fetch_and_normalise()
    assert norm.norms[0].norm_id == "art:1"


def test_eprivacy_source_url_propagated():
    """The resolved XML URL must be stored on NormalizedLaw.source_url."""
    fake_url = "https://example.invalid/eprivacy.xml"
    act = EPrivacyAct(
        resolve_xml_url=lambda celex, lang: fake_url,
        http_get=lambda url: FAKE_XML,
    )
    norm = act.fetch_and_normalise()
    assert norm.source_url == fake_url


def test_eprivacy_display_name():
    fake_url = "https://example.invalid/eprivacy.xml"
    act = EPrivacyAct(
        resolve_xml_url=lambda celex, lang: fake_url,
        http_get=lambda url: FAKE_XML,
    )
    norm = act.fetch_and_normalise()
    assert "2002/58" in norm.display_name
