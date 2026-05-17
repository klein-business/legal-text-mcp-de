# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from prepare_data.state_law.nds import NDSStateLaw


INDEX_HTML = """
<html><body>
  <table class="law-table">
    <tr><td><a href="/voris/foo">Niedersächsische Bauordnung (NBauO)</a></td></tr>
    <tr><td><a href="/voris/bar">Strassengesetz Niedersachsen (NStrG)</a></td></tr>
    <tr><td><a href="">empty</a></td></tr>
    <tr><td><a href="/x">No Brackets</a></td></tr>
  </table>
</body></html>
"""

LAW_HTML = """
<html><body>
  <h1>Niedersächsische Bauordnung</h1>
  <div class="voris-norm" id="par-1">
    <h2>§ 1 Anwendungsbereich</h2>
    <p class="voris-text">Diese Bauordnung gilt für bauliche Anlagen.</p>
  </div>
</body></html>
"""


def test_nds_normalises_a_law():
    def fake_get(url: str) -> str:
        return INDEX_HTML if "nav=lawList" in url else LAW_HTML

    nds = NDSStateLaw(http_get=fake_get)
    index = nds.fetch_index()
    assert len(index) == 2
    assert index[0].law_id == "NBauO"
    assert index[1].law_id == "NStrG"

    raw = nds.fetch_law(index[0].law_id)
    norm = nds.normalize(raw)
    assert norm.canonical_id.startswith("nds/")
    assert norm.state_code == "nds"
    assert norm.display_code == "NBauO"
    assert len(norm.norms) == 1
    assert norm.norms[0].title == "Anwendungsbereich"
    assert "bauliche Anlagen" in norm.norms[0].text


def test_nds_skips_invalid_index_entries():
    HTML = """<html><body><table class="law-table">
      <tr><td><a href="/x">No Brackets Here</a></td></tr>
      <tr><td><a href="">empty</a></td></tr>
    </table></body></html>"""
    nds = NDSStateLaw(http_get=lambda url: HTML)
    assert nds.fetch_index() == []
