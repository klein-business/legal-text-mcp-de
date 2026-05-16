# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import zipfile

from legal_text_mcp_de.legal_texts.gii_xml import parse_gii_zip


def test_gii_parser_extracts_paragraph_and_subdivision(tmp_path):
    xml = """<dokumente><norm><metadaten><enbez>§ 5</enbez><titel>Testnorm</titel></metadaten><textdaten><text><Content><P>(1) Anbieter informieren Verbraucher. Zweiter Satz.</P></Content></text></textdaten></norm></dokumente>"""
    zip_path = tmp_path / "xml.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("law.xml", xml)
    source = {"source_metadata": {"source_path": "ddg"}, "source_url": "https://www.gesetze-im-internet.de/ddg/xml.zip", "source_kind": "gesetze-im-internet"}
    law = {"canonical_id": "ddg"}
    norms = parse_gii_zip(zip_path, law, source)
    assert norms[0]["norm_id"] == "par:5"
    assert norms[0]["subdivisions"][0]["path"] == "abs:1"


def test_gii_parser_extracts_egbgb_article_child(tmp_path):
    xml = """<dokumente>
    <norm><metadaten><gliederungseinheit><gliederungsbez>Art 246a</gliederungsbez><gliederungstitel>Informationspflichten</gliederungstitel></gliederungseinheit></metadaten><textdaten><text><Content /></text></textdaten></norm>
    <norm><metadaten><gliederungseinheit><gliederungsbez>Art 246a</gliederungsbez></gliederungseinheit><enbez>§ 1</enbez><titel>Informationen</titel></metadaten><textdaten><text><Content><P>(1) Der Unternehmer informiert.</P></Content></text></textdaten></norm>
    </dokumente>"""
    zip_path = tmp_path / "xml.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr("law.xml", xml)
    source = {"source_metadata": {"source_path": "bgbeg"}, "source_url": "https://www.gesetze-im-internet.de/bgbeg/xml.zip", "source_kind": "gesetze-im-internet"}
    norms = parse_gii_zip(zip_path, {"canonical_id": "egbgb"}, source)
    assert norms[0]["norm_id"] == "art:246a"
    assert norms[1]["norm_id"] == "art:246a/par:1"
