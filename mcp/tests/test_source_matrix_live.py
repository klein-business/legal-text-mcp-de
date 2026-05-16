# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import urllib.request

from legal_texts.sources import SOURCE_SPECS


def fetch_status(url):
    request = urllib.request.Request(url, headers={"User-Agent": "legal-text-mcp-de-tests/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, response.headers.get("content-type", ""), response.read(4096)
    except Exception as exc:
        if hasattr(exc, "code"):
            return exc.code, getattr(exc, "headers", {}).get("content-type", ""), b""
        raise


def test_representative_live_source_matrix_probes():
    for law_id in ["bgb", "egbgb", "tdddg", "pangv_2022"]:
        spec = SOURCE_SPECS[law_id]
        status, _, _ = fetch_status(spec.index_url)
        assert status == 200
    status, content_type, body = fetch_status(SOURCE_SPECS["dsgvo_eu_2016_679"].source_url)
    assert status == 200
    assert "xml" in content_type.lower()
    text = body.decode("utf-8", errors="replace")
    assert "<LG.DOC>DE</LG.DOC>" in text


def test_live_known_invalid_paths_remain_invalid():
    for url in [
        "https://www.gesetze-im-internet.de/tddsg/index.html",
        "https://www.gesetze-im-internet.de/pangv/index.html",
    ]:
        status, _, _ = fetch_status(url)
        assert status == 404
