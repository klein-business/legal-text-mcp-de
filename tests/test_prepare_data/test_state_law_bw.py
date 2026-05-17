# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from prepare_data.state_law.bw import BWStateLaw


INDEX_HTML = """
<html><body>
  <ul class="law-list">
    <li><a href="/jportal/portal/t/foo">Landesbauordnung BW (LBO BW)</a></li>
    <li><a href="/jportal/portal/t/bar">Naturschutzgesetz BW (NatSchG BW)</a></li>
    <li><a href="">no href</a></li>
    <li><a href="/x">No Brackets</a></li>
  </ul>
</body></html>
"""

LAW_HTML = """
<html><body>
  <h1>Landesbauordnung Baden-Württemberg</h1>
  <div class="jnnorm" id="par-1">
    <h2>§ 1 Anwendungsbereich</h2>
    <p class="jurAbsatz">Dieses Gesetz gilt für bauliche Anlagen in Baden-Württemberg.</p>
  </div>
</body></html>
"""


def test_bw_normalises_a_law():
    def fake_get(url: str) -> str:
        return INDEX_HTML if "nav=lawList" in url else LAW_HTML

    bw = BWStateLaw(http_get=fake_get)
    index = bw.fetch_index()
    assert len(index) == 2  # 2 valid entries; 2 invalid skipped
    assert index[0].law_id == "LBO BW"
    assert index[1].law_id == "NatSchG BW"

    raw = bw.fetch_law(index[0].law_id)
    norm = bw.normalize(raw)
    assert norm.canonical_id.startswith("bw/")
    assert norm.state_code == "bw"
    assert norm.display_code == "LBO BW"
    assert len(norm.norms) == 1
    assert norm.norms[0].title == "Anwendungsbereich"
    assert "bauliche Anlagen" in norm.norms[0].text


def test_bw_skips_invalid_index_entries():
    HTML = """<html><body><ul class="law-list">
      <li><a href="/x">No Brackets Here</a></li>
      <li><a href="">empty href</a></li>
      <li><a href="/y"></a></li>
    </ul></body></html>"""
    bw = BWStateLaw(http_get=lambda url: HTML)
    assert bw.fetch_index() == []
