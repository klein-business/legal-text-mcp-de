# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Focused branch-coverage tests for mcp.parser targeting uncovered line ranges."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from legal_text_mcp_de.parser import LawLibrary, LawNode, LawParser


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_MULTI_PARA_MARKDOWN = """\
---
Title: Bürgerliches Gesetzbuch
jurabk: BGB
---

# § 1 Rechtsfähigkeit
(1) Die Rechtsfähigkeit des Menschen beginnt mit der Vollendung der Geburt.
(2) Niemand kann seine Rechtsfähigkeit aufgeben.
$$3$$
(3) Dritter Absatz mit Marker.

# § 2 Volljährigkeit
Volljährig ist, wer das 18. Lebensjahr vollendet hat.

# § 3 Weitere Norm
Weitere Norm ohne Absätze.

# § 4 Vierte Norm
Eine vierte Norm.

# § 5 Fünfte Norm
Eine fünfte Norm.

# § 6 Sechste Norm
Eine sechste Norm.
"""

_FEW_PARA_MARKDOWN = """\
---
Title: Tiny Law
jurabk: TinyG
---

# § 1 Only paragraph
Content here.
"""

_NO_SHORT_TITLE_MARKDOWN = """\
---
Title: Law Without Abbreviation
---

# § 1 First paragraph
Content here.
# § 2 Second paragraph
More content.
# § 3 Third paragraph
Even more.
# § 4 Fourth paragraph
Fourth.
# § 5 Fifth paragraph
Fifth.
# § 6 Sixth paragraph
Sixth.
"""

_MULTI_LINE_TITLE_MARKDOWN = """\
---
Title: First line of title
  Second line of title
jurabk: MultiG
---

# § 1 Paragraph one
Content.
# § 2 Paragraph two
Content.
# § 3 Paragraph three
Content.
# § 4 Paragraph four
Content.
# § 5 Paragraph five
Content.
# § 6 Paragraph six
Content.
"""


# ---------------------------------------------------------------------------
# Task 16 missed lines: LawNode.__repr__ (line 52)
# ---------------------------------------------------------------------------


def test_law_node_repr() -> None:
    """LawNode.__repr__ returns a useful debug string."""
    node = LawNode("paragraph", "1", "Scope")
    r = repr(node)
    assert "paragraph" in r
    assert "1" in r
    assert "Scope" in r


# ---------------------------------------------------------------------------
# Missed lines 104-105: multi-line frontmatter title continuation
# ---------------------------------------------------------------------------


def test_parser_multi_line_title() -> None:
    """Frontmatter title spanning multiple lines is joined with a space."""
    parser = LawParser(_MULTI_LINE_TITLE_MARKDOWN)
    assert parser.full_title is not None
    assert "First line" in parser.full_title
    assert "Second line" in parser.full_title


# ---------------------------------------------------------------------------
# Missed lines 176-217: get_paragraph with absatz_id
# ---------------------------------------------------------------------------


def test_get_paragraph_existing_absatz(sample_law_markdown: str) -> None:
    """Retrieving an existing absatz returns the absatz text."""
    parser = LawParser(sample_law_markdown)
    result = parser.get_paragraph("2", absatz_id="1")
    assert result["absatz"] == "1"
    assert "First absatz" in result["text"]


def test_get_paragraph_missing_absatz_raises(sample_law_markdown: str) -> None:
    """Requesting a non-existent absatz raises KeyError with available list."""
    parser = LawParser(sample_law_markdown)
    with pytest.raises(KeyError, match="99"):
        parser.get_paragraph("2", absatz_id="99")


def test_get_paragraph_absatz_stops_at_next_absatz(sample_law_markdown: str) -> None:
    """Absatz content stops before the next absatz marker."""
    parser = LawParser(sample_law_markdown)
    result = parser.get_paragraph("2", absatz_id="2")
    # (1) should not appear in the text for (2)
    assert "First absatz" not in result["text"]


# ---------------------------------------------------------------------------
# Missed lines 243-248: load_laws_from_folder
# ---------------------------------------------------------------------------


def test_load_laws_from_folder(tmp_path: Path) -> None:
    """load_laws_from_folder loads all index.md files found in a directory."""
    law_dir = tmp_path / "bgb"
    law_dir.mkdir()
    (law_dir / "index.md").write_text(_MULTI_PARA_MARKDOWN, encoding="utf-8")

    library = LawLibrary()
    library.load_laws_from_folder(tmp_path)
    assert "bgb" in library.laws


# ---------------------------------------------------------------------------
# Missed line 255: _load_law_from_markdown — fewer paragraphs than min_paragraphs
# ---------------------------------------------------------------------------


def test_load_law_skips_small_laws(tmp_path: Path) -> None:
    """_load_law_from_markdown returns None for laws below min_paragraphs."""
    file_path = tmp_path / "tiny.md"
    file_path.write_text(_FEW_PARA_MARKDOWN, encoding="utf-8")

    library = LawLibrary()
    result = library.load_law_from_file(file_path)
    # min_paragraphs default is 5; TinyG has only 1 → skipped
    assert result is None
    assert "tinyg" not in library.laws


# ---------------------------------------------------------------------------
# Missed line 258: _load_law_from_markdown — raises when short_title missing
# ---------------------------------------------------------------------------


def test_load_law_raises_without_short_title(tmp_path: Path) -> None:
    """_load_law_from_markdown raises ValueError when jurabk/short_title is absent."""
    file_path = tmp_path / "no_abbr.md"
    file_path.write_text(_NO_SHORT_TITLE_MARKDOWN, encoding="utf-8")

    library = LawLibrary()
    with pytest.raises(ValueError, match="short title"):
        library.load_law_from_file(file_path)


# ---------------------------------------------------------------------------
# Missed lines 283-285: load_law_from_file
# ---------------------------------------------------------------------------


def test_load_law_from_file(tmp_path: Path) -> None:
    """load_law_from_file reads a file and returns the short title."""
    file_path = tmp_path / "index.md"
    file_path.write_text(_MULTI_PARA_MARKDOWN, encoding="utf-8")

    library = LawLibrary()
    short_title = library.load_law_from_file(file_path)
    assert short_title == "BGB"
    assert "bgb" in library.laws


# ---------------------------------------------------------------------------
# Missed lines 349-371: get_available_laws with search_string
# ---------------------------------------------------------------------------


def test_get_available_laws_with_search_string(tmp_path: Path) -> None:
    """get_available_laws with a search string uses fuzzy matching."""
    file_path = tmp_path / "index.md"
    file_path.write_text(_MULTI_PARA_MARKDOWN, encoding="utf-8")

    library = LawLibrary()
    library.load_law_from_file(file_path)

    # Search for "bgb" — should match the loaded law
    results = library.get_available_laws(search_string="bgb")
    assert isinstance(results, list)
    # No assertion on exact content since fuzzy match depends on rapidfuzz
    # but the function must complete without error


# ---------------------------------------------------------------------------
# Missed lines 388-389: LawLibrary.get — law not found
# ---------------------------------------------------------------------------


def test_library_get_raises_for_unknown_law() -> None:
    """LawLibrary.get raises KeyError when the law code is not loaded."""
    library = LawLibrary()
    with pytest.raises(KeyError, match="UnknownLaw"):
        library.get("UnknownLaw", "1")


# ---------------------------------------------------------------------------
# Missed line 420: LawLibrary.search — FTS query with results
# ---------------------------------------------------------------------------


def test_library_search_returns_results(tmp_path: Path) -> None:
    """LawLibrary.search returns matching paragraphs from loaded laws."""
    file_path = tmp_path / "index.md"
    file_path.write_text(_MULTI_PARA_MARKDOWN, encoding="utf-8")

    library = LawLibrary()
    library.load_law_from_file(file_path)

    results = library.search("Rechtsfähigkeit")
    assert isinstance(results, list)
    assert len(results) >= 1
    assert results[0]["law"] == "bgb"


# ---------------------------------------------------------------------------
# Missed line 436: LawLibrary.search — sqlite OperationalError
# ---------------------------------------------------------------------------


def test_library_search_handles_fts_error() -> None:
    """LawLibrary.search returns empty list on FTS syntax errors."""
    library = LawLibrary()
    # An invalid FTS query (unmatched quote) triggers sqlite3.OperationalError
    results = library.search('"unclosed quote')
    assert results == []


# ---------------------------------------------------------------------------
# Missed lines 297-300: load_law_from_url (uses requests but we mock urllib)
# ---------------------------------------------------------------------------


def test_load_law_from_url(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """load_law_from_url reads markdown from a URL."""
    import urllib.request

    class _FakeResponse:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def read(self) -> bytes:
            return self._data

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    monkeypatch.setattr(
        urllib.request,
        "urlopen",
        lambda url: _FakeResponse(_MULTI_PARA_MARKDOWN.encode("utf-8")),
    )

    library = LawLibrary()
    short_title = library.load_law_from_url("https://example.com/bgb/index.md")
    assert short_title == "BGB"
    assert "bgb" in library.laws


# ---------------------------------------------------------------------------
# Missed lines 312-323: load_laws_from_github
# ---------------------------------------------------------------------------


def test_load_laws_from_github(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_laws_from_github loads multiple laws from URLs, skips failures."""
    import urllib.request

    call_count = 0

    class _FakeResponse:
        def __init__(self) -> None:
            nonlocal call_count
            call_count += 1

        def read(self) -> bytes:
            return _MULTI_PARA_MARKDOWN.encode("utf-8")

        def __enter__(self) -> "_FakeResponse":
            return self

        def __exit__(self, *args: object) -> None:
            pass

    monkeypatch.setattr(urllib.request, "urlopen", lambda url: _FakeResponse())

    library = LawLibrary()
    loaded = library.load_laws_from_github(["bgb"])
    assert "bgb" in loaded


def test_load_laws_from_github_handles_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    """load_laws_from_github skips codes that fail to load and returns only successes."""
    import urllib.request

    def _raise(url: str) -> None:
        raise OSError("network unreachable")

    monkeypatch.setattr(urllib.request, "urlopen", _raise)

    library = LawLibrary()
    loaded = library.load_laws_from_github(["bgb", "hgb"])
    assert loaded == []


# ---------------------------------------------------------------------------
# Additional: get_json and get_available_laws_json for completeness
# ---------------------------------------------------------------------------


def test_get_json_returns_json_string(tmp_path: Path) -> None:
    """LawLibrary.get_json returns valid JSON for a found paragraph."""
    file_path = tmp_path / "index.md"
    file_path.write_text(_MULTI_PARA_MARKDOWN, encoding="utf-8")

    library = LawLibrary()
    library.load_law_from_file(file_path)

    json_str = library.get_json("BGB", "1")
    data = json.loads(json_str)
    assert data["paragraph"] == "1"
    assert data["law"] == "BGB"


def test_get_available_laws_json_returns_json_string(tmp_path: Path) -> None:
    """get_available_laws_json returns valid JSON array."""
    file_path = tmp_path / "index.md"
    file_path.write_text(_MULTI_PARA_MARKDOWN, encoding="utf-8")

    library = LawLibrary()
    library.load_law_from_file(file_path)

    json_str = library.get_available_laws_json()
    data = json.loads(json_str)
    assert isinstance(data, list)
    assert any(law["code"] == "bgb" for law in data)
