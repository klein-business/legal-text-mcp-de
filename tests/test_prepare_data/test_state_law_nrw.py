# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from prepare_data.state_law.nrw import NRWStateLaw


INDEX_HTML = """
<html><body>
  <table class="lawList">
    <tr>
      <td>
        <a href="/lmi/owa/br_bes_text?anw_nr=2&amp;gld_nr=2&amp;ugl_nr=20&amp;bes_id=23456">
          Bauordnung NRW (BauO NRW)
        </a>
      </td>
    </tr>
    <tr>
      <td>
        <a href="/lmi/owa/br_bes_text?anw_nr=2&amp;gld_nr=99&amp;ugl_nr=1">
          Strassengesetz NRW (StrWG NRW)
        </a>
      </td>
    </tr>
  </table>
</body></html>
"""

LAW_HTML = """
<html><body>
  <h1>Bauordnung NRW</h1>
  <div class="paragraph" id="§-1">
    <h3>§ 1 Anwendungsbereich</h3>
    <p>Dieses Gesetz gilt für bauliche Anlagen.</p>
  </div>
  <div class="paragraph" id="§-2">
    <h3>§ 2 Begriffsbestimmungen</h3>
    <p>Im Sinne dieses Gesetzes …</p>
  </div>
</body></html>
"""


def test_nrw_normalises_a_law_with_two_paragraphs():
    def fake_get(url: str) -> str:
        if "br_bes_lst" in url:
            return INDEX_HTML
        return LAW_HTML

    nrw = NRWStateLaw(http_get=fake_get)
    index = nrw.fetch_index()
    assert len(index) == 2
    assert index[0].law_id == "BauO NRW"
    assert index[1].law_id == "StrWG NRW"

    raw = nrw.fetch_law(index[0].law_id)
    norm = nrw.normalize(raw)
    assert norm.canonical_id.startswith("nrw/")
    assert norm.state_code == "nrw"
    assert norm.display_code == "BauO NRW"
    assert len(norm.norms) == 2
    assert norm.norms[0].title == "Anwendungsbereich"
    assert "bauliche Anlagen" in norm.norms[0].text


def test_nrw_skips_links_without_abbrev_or_text():
    HTML = """<html><body><table class="lawList">
      <tr><td><a href="/x">No Brackets Here</a></td></tr>
      <tr><td><a href=""></a></td></tr>
    </table></body></html>"""
    nrw = NRWStateLaw(http_get=lambda url: HTML)
    # First link has text but no bracketed abbrev — should be skipped
    # Second link has neither text nor href — should be skipped
    assert nrw.fetch_index() == []
