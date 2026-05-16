# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Cover the dataclass to_dict serialisers and normalisation helpers in models.py.

Lifts models.py from 85% to 100% by serialising every record type and
exercising canonical_norm_id / normalize_unit edge cases.
"""

from __future__ import annotations

import pytest

from legal_text_mcp_de.legal_texts.models import (
    CitationSelection,
    LawRecord,
    NormRecord,
    Readiness,
    SourceMetadata,
    SubdivisionRecord,
    canonical_citation_id,
    canonical_norm_id,
    drop_none,
    normalize_unit,
    normalize_value,
)


def test_drop_none_removes_none_values_only() -> None:
    assert drop_none({"a": 1, "b": None, "c": "x"}) == {"a": 1, "c": "x"}


def test_source_metadata_to_dict_drops_none() -> None:
    m = SourceMetadata(
        source_kind="gesetze-im-internet",
        source_identifier="bgb",
        source_url="https://example.invalid/bgb",
        retrieved_at="2026-05-16T00:00:00Z",
        stand_date=None,
        stand_date_status="not_exposed",
        content_hash="abc",
    )
    d = m.to_dict()
    assert "stand_date" not in d
    assert d["content_hash"] == "abc"


def test_law_record_to_dict_drops_optional_none() -> None:
    r = LawRecord(
        canonical_id="bgb",
        display_code="BGB",
        display_name="Bürgerliches Gesetzbuch",
        source={},
        aliases=[],
        norm_count=2400,
        stand_date=None,
    )
    d = r.to_dict()
    assert "stand_date" not in d
    assert d["norm_count"] == 2400


def test_subdivision_record_to_dict_keeps_all_fields() -> None:
    s = SubdivisionRecord(kind="absatz", value="1", text="Wer …", path="par:5/abs:1")
    d = s.to_dict()
    assert d == {"kind": "absatz", "value": "1", "text": "Wer …", "path": "par:5/abs:1"}


def test_norm_record_to_dict_drops_empty_collections_and_none_text() -> None:
    n = NormRecord(
        canonical_id="bgb/par:5",
        law_id="bgb",
        norm_id="par:5",
        unit="par",
        value="5",
        title="Beispieltitel",
        text=None,
        status="active",
        url="https://example.invalid/bgb/5",
        source={"source_url": "..."},
    )
    d = n.to_dict()
    assert "text" not in d
    assert "subdivisions" not in d
    assert "children" not in d
    assert "known_issues" not in d
    assert d["status"] == "active"


def test_norm_record_to_dict_keeps_populated_collections() -> None:
    n = NormRecord(
        canonical_id="bgb/par:5",
        law_id="bgb",
        norm_id="par:5",
        unit="par",
        value="5",
        title="Beispiel",
        text="Some text.",
        status="active",
        url="https://example.invalid/bgb/5",
        source={"source_url": "..."},
        subdivisions=[{"kind": "absatz", "value": "1"}],
        children=["bgb/par:5/abs:1"],
        known_issues=[{"code": "X"}],
    )
    d = n.to_dict()
    assert d["text"] == "Some text."
    assert d["subdivisions"] == [{"kind": "absatz", "value": "1"}]
    assert d["children"] == ["bgb/par:5/abs:1"]
    assert d["known_issues"] == [{"code": "X"}]


def test_citation_selection_to_dict_drops_none() -> None:
    c = CitationSelection(
        requested_path="§5 BGB",
        resolved_path="bgb/par:5",
        subdivisions=[],
        text="…",
        known_issues=None,
    )
    d = c.to_dict()
    assert "known_issues" not in d
    assert d["resolved_path"] == "bgb/par:5"


def test_readiness_to_dict_keeps_explicit_keys() -> None:
    r = Readiness(stage="serving_dataset", state="ready", details={"path": "/x"})
    assert r.to_dict() == {
        "stage": "serving_dataset",
        "state": "ready",
        "details": {"path": "/x"},
    }


# ---------- normalisation helpers ----------


@pytest.mark.parametrize(
    "raw_unit,expected",
    [
        ("§", "par"),
        ("par", "par"),
        ("Art", "art"),
        ("Article", "art"),
        ("recital", "recital"),
        ("Erwägungsgrund", "recital"),
        ("Erwg.", "recital"),
        ("Chapter", "chapter"),
        ("Kapitel", "chapter"),
        ("Section", "section"),
        ("Abschnitt", "section"),
        ("Annex", "annex"),
        ("Anhang", "annex"),
        ("container", "container"),
    ],
)
def test_normalize_unit_known_inputs(raw_unit: str, expected: str) -> None:
    assert normalize_unit(raw_unit) == expected


def test_normalize_unit_rejects_unknown() -> None:
    with pytest.raises(ValueError) as exc_info:
        normalize_unit("frobnicate")
    assert "frobnicate" in str(exc_info.value)


def test_normalize_value_lowercases_and_strips() -> None:
    assert normalize_value(" 5 ") == "5"
    assert normalize_value("II A") == "iia"


def test_canonical_norm_id_combines_unit_and_value() -> None:
    assert canonical_norm_id("§", "5") == "par:5"
    assert canonical_norm_id("Article", "12") == "art:12"


def test_canonical_citation_id_combines_law_and_norm() -> None:
    assert canonical_citation_id("bgb", "par:5") == "bgb/par:5"
