# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from prepare_data.state_law.bayern import BayernStateLaw


def test_bayern_normalises_one_law_from_fixture():
    raw_index_html = """
    <ul>
      <li><a href="/Content/Document/BayBO">Bayerische Bauordnung (BayBO)</a></li>
    </ul>
    """
    raw_law_html = """
    <html><body>
      <h1>Bayerische Bauordnung (BayBO)</h1>
      <article id="art-1"><h2>Art. 1 Geltungsbereich</h2><p>Dieses Gesetz gilt …</p></article>
    </body></html>
    """

    def fake_get(url: str) -> str:
        return raw_index_html if "DocumentList" in url else raw_law_html

    bayern = BayernStateLaw(http_get=fake_get)
    index = bayern.fetch_index()
    assert len(index) == 1
    assert index[0].law_id == "BayBO"

    raw = bayern.fetch_law("BayBO")
    norm = bayern.normalize(raw)
    assert norm.canonical_id == "by/baybo"
    assert norm.display_code == "BayBO"
    assert norm.state_code == "by"
    assert len(norm.norms) == 1
    assert norm.norms[0].title == "Geltungsbereich"
    assert "Dieses Gesetz gilt" in norm.norms[0].text


def test_bayern_emits_empty_index_for_empty_html():
    bayern = BayernStateLaw(http_get=lambda url: "<html><body></body></html>")
    assert bayern.fetch_index() == []
