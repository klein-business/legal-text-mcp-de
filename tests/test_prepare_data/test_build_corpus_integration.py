# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import tarfile
from pathlib import Path
from unittest.mock import patch

import zstandard

from prepare_data.build_corpus import main


BAYERN_INDEX_HTML = """
<html><body><ul>
  <li><a href="/Content/Document/BayBO">BayBO</a></li>
</ul></body></html>
"""

BAYERN_LAW_HTML = """
<html><body>
  <h1>BayBO</h1>
  <article id="art-1"><h2>Art. 1 Test</h2><p>Hello</p></article>
</body></html>
"""


def _fake_bayern_get(url: str) -> str:
    return BAYERN_INDEX_HTML if "DocumentList" in url else BAYERN_LAW_HTML


def test_build_corpus_with_state_law_source_produces_bundle_with_bayern(tmp_path: Path):
    out = tmp_path / "corpus.tar.zst"
    with patch("prepare_data.state_law.bayern._default_http_get", side_effect=_fake_bayern_get):
        rc = main(["--output", str(out), "--sources", "land:by"])
    assert rc == 0
    assert out.exists()
    # Verify the bundle contains the Bayern law
    with open(out, "rb") as f:
        dctx = zstandard.ZstdDecompressor()
        with dctx.stream_reader(f) as reader:
            with tarfile.open(fileobj=reader, mode="r|") as tar:
                names = tar.getnames()
    assert "manifest.json" in names
    assert "laws/by/baybo.json" in names
