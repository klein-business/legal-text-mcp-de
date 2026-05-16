# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import pytest

from legal_text_mcp_de.legal_texts.errors import AMBIGUOUS_LAW_ALIAS, LAW_NOT_FOUND, LegalTextError
from legal_text_mcp_de.legal_texts.registry import LawRegistry


def test_required_aliases_resolve():
    registry = LawRegistry.load()
    cases = {
        "BGB": "bgb",
        "Bürgerliches Gesetzbuch": "bgb",
        "BGBEG": "egbgb",
        "UWG": "uwg_2004",
        "TTDSG": "tdddg",
        "tddsg": "tdddg",
        "BDSG": "bdsg_2018",
        "PAngV": "pangv_2022",
        "pangv": "pangv_2022",
        "DSGVO": "dsgvo_eu_2016_679",
        "GDPR": "dsgvo_eu_2016_679",
    }
    for alias, canonical_id in cases.items():
        assert registry.resolve_law(alias)["canonical_id"] == canonical_id


def test_source_path_separation_for_historical_aliases():
    registry = LawRegistry.load()
    assert registry.resolve_law("tddsg")["source_identifier"] == "ttdsg"
    assert registry.resolve_law("pangv")["source_identifier"] == "pangv_2022"


def test_unknown_law_has_structured_error():
    registry = LawRegistry.load()
    with pytest.raises(LegalTextError) as exc:
        registry.resolve_law("nope")
    assert exc.value.code == LAW_NOT_FOUND
    assert exc.value.to_dict()["error"]["suggestions"]


def test_ambiguous_alias_error_is_available_for_non_validating_registry():
    entries = [
        {"canonical_id": "a", "display_code": "A", "display_name": "A", "source_kind": "gesetze-im-internet", "source_identifier": "a", "aliases": ["X"]},
        {"canonical_id": "b", "display_code": "B", "display_name": "B", "source_kind": "gesetze-im-internet", "source_identifier": "b", "aliases": ["X"]},
    ]
    registry = LawRegistry.from_entries(entries, validate=False)
    with pytest.raises(LegalTextError) as exc:
        registry.resolve_law("x")
    assert exc.value.code == AMBIGUOUS_LAW_ALIAS
