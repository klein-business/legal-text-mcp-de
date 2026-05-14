from legal_texts.eurlex_xml import parse_dsgvo_xml


def test_eurlex_parser_requires_doc2_article_xml(tmp_path):
    xml_path = tmp_path / "dsgvo.xml"
    xml_path.write_text("<ROOT><LG.DOC>DE</LG.DOC><ACT><ARTICLE IDENTIFIER=\"005\"><TI.ART>Artikel 5</TI.ART><P>Personenbezogene Daten.</P></ARTICLE></ACT></ROOT>")
    source = {
        "source_url": "https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_2",
        "source_kind": "eur-lex-cellar",
        "source_metadata": {"document": "DOC_2"},
    }
    norms = parse_dsgvo_xml(xml_path, {"canonical_id": "dsgvo_eu_2016_679"}, source)
    assert norms[0]["norm_id"] == "art:5"
    assert norms[0]["source"]["source_kind"] == "eur-lex-cellar"


def test_eurlex_parser_rejects_metadata_only_doc1(tmp_path):
    xml_path = tmp_path / "doc1.xml"
    xml_path.write_text("<ROOT><LG.DOC>DE</LG.DOC><REF.PHYS>DOC_2</REF.PHYS></ROOT>")
    try:
        parse_dsgvo_xml(xml_path, {"canonical_id": "dsgvo_eu_2016_679"}, {})
        assert False
    except ValueError:
        pass
