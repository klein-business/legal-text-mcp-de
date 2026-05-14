from legal_texts.importer import diff_manifests, probe_known_invalid, probe_source, validate_dsgvo_doc2
from legal_texts.sources import SOURCE_SPECS


def fake_fetch(url):
    if "tddsg" in url or "/pangv/" in url:
        return 404, {"content-type": "text/html"}, b"missing"
    body = b"<LG.DOC>DE</LG.DOC><ACT><ARTICLE IDENTIFIER=\"005\">Artikel 5</ARTICLE></ACT>" if "DOC_2" in url else b"zip-bytes"
    return 200, {"content-type": "application/xml"}, body


def test_probe_source_uses_expected_urls():
    result = probe_source(SOURCE_SPECS["dsgvo_eu_2016_679"], fetch=fake_fetch)
    assert result["results"][0]["status"] == 200


def test_dsgvo_doc2_validation_rejects_metadata_only_xml():
    try:
        validate_dsgvo_doc2(b"<LG.DOC>DE</LG.DOC><REF.PHYS>DOC_2</REF.PHYS>")
        assert False
    except Exception as exc:
        assert "DOC_2" in str(exc) or "article" in str(exc)


def test_known_invalid_probes_expect_404():
    results = probe_known_invalid(fetch=fake_fetch)
    assert {item["status"] for item in results} == {404}


def test_manifest_diff_detects_changes():
    old = {"entries": [{"canonical_id": "bgb", "source": {"content_hash": "1"}}]}
    new = {"entries": [{"canonical_id": "bgb", "source": {"content_hash": "2"}}]}
    assert diff_manifests(old, new)["changed"] == ["bgb"]
