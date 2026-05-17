# tests/test_prepare_data/test_state_law_he.py
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from prepare_data.state_law.he import HEStateLaw


INDEX_HTML = """
<html><body>
  <ul class="rechtsliste">
    <li><a href="/bshe/document/foo">Hessische Bauordnung (HBO)</a></li>
    <li><a href="/bshe/document/bar">Hessisches Naturschutzgesetz (HENatG)</a></li>
    <li><a href="">empty</a></li>
    <li><a href="/x">No Brackets</a></li>
  </ul>
</body></html>
"""

LAW_HTML = """
<html><body>
  <h1>Hessische Bauordnung</h1>
  <div class="rv-norm" id="par-1">
    <h3>§ 1 Geltungsbereich</h3>
    <p class="rv-text">Diese Bauordnung gilt im Land Hessen.</p>
  </div>
</body></html>
"""


def test_he_normalises_a_law():
    def fake_get(url: str) -> str:
        return INDEX_HTML if "bla=BgRecht" in url else LAW_HTML

    he = HEStateLaw(http_get=fake_get)
    index = he.fetch_index()
    assert len(index) == 2
    assert index[0].law_id == "HBO"
    assert index[1].law_id == "HENatG"

    raw = he.fetch_law(index[0].law_id)
    norm = he.normalize(raw)
    assert norm.canonical_id.startswith("he/")
    assert norm.state_code == "he"
    assert norm.display_code == "HBO"
    assert len(norm.norms) == 1
    assert norm.norms[0].title == "Geltungsbereich"
    assert "Land Hessen" in norm.norms[0].text


def test_he_skips_invalid_index_entries():
    HTML = """<html><body><ul class="rechtsliste">
      <li><a href="/x">No Brackets Here</a></li>
      <li><a href="">empty</a></li>
    </ul></body></html>"""
    he = HEStateLaw(http_get=lambda url: HTML)
    assert he.fetch_index() == []
