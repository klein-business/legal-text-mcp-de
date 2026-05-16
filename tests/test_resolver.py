# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path
import json

import pytest

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.errors import INVALID_CITATION, NORM_NOT_FOUND, LegalTextError
from legal_text_mcp_de.legal_texts.resolver import get_norm, resolve_citation


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"
GENERATED_PACKAGE = Path(__file__).parent / "fixtures" / "generated_package"


@pytest.fixture
def dataset():
    return NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True)


def test_resolve_required_norm_and_alias(dataset):
    result = resolve_citation(dataset, "UWG", "par", "5a")
    assert result["law"]["canonical_id"] == "uwg_2004"
    assert result["norm"]["norm_id"] == "par:5a"
    assert result["source"]["source_kind"] == "gesetze-im-internet"


def test_egbgb_container_and_child(dataset):
    container = resolve_citation(dataset, "EGBGB", "art", "246a")
    child = resolve_citation(dataset, "EGBGB", "art", "246a", child_unit="par", child_value="1")
    assert container["norm"]["status"] == "container"
    assert "egbgb/art:246a/par:1" in container["norm"]["children"]
    assert child["norm"]["canonical_id"] == "egbgb/art:246a/par:1"


def test_egbgb_container_records_precise_upstream_url_anomaly(dataset):
    container = resolve_citation(dataset, "EGBGB", "art", "246a")

    assert container["norm"]["known_issues"] == [
        {
            "code": "UPSTREAM_CONTAINER_URL_UNAVAILABLE",
            "url": "https://www.gesetze-im-internet.de/bgbeg/art_246a.html",
            "http_status": 404,
            "note": "Upstream GII container URL returns 404; child URL is verified separately.",
        }
    ]


def test_get_norm_parses_encoded_canonical_child(dataset):
    result = get_norm(dataset, "egbgb", "art:246a/par:1")
    assert result["citation"]["label"] == "EGBGB Art. 246a § 1"


def test_generated_package_recital_lookup():
    generated = NormalizedDataset.load(GENERATED_PACKAGE, require_search_index=True)
    result = get_norm(generated, "DSGVO", "recital:1")
    assert result["norm"]["canonical_id"] == "dsgvo_eu_2016_679/recital:1"
    assert result["citation"]["label"] == "DSGVO ErwG 1"


def test_generated_unit_lookups_without_changing_article_child_behavior(tmp_path):
    laws = json.loads((GENERATED_PACKAGE / "laws.json").read_text(encoding="utf-8"))
    base_source = laws[0]["source"]
    generated_values = {
        "chapter": "overview",
        "section": "scope-1",
        "annex": "a_1",
        "container": "recitals",
    }
    unit_norms = [
        {
            "canonical_id": f"dsgvo_eu_2016_679/{unit}:{value}",
            "law_id": "dsgvo_eu_2016_679",
            "norm_id": f"{unit}:{value}",
            "unit": unit,
            "value": value,
            "title": f"{unit} {value}",
            "text": None if unit == "container" else f"{unit} text",
            "status": "container" if unit == "container" else "active",
            "url": f"https://example.test/{unit}/{value}",
            "source": base_source,
        }
        for unit, value in generated_values.items()
    ]
    norms = json.loads((GENERATED_PACKAGE / "norms.json").read_text(encoding="utf-8")) + unit_norms
    package = tmp_path / "legacy-units"
    package.mkdir()
    (package / "laws.json").write_text(json.dumps(laws), encoding="utf-8")
    (package / "norms.json").write_text(json.dumps(norms), encoding="utf-8")

    generated_units = NormalizedDataset.load(package)
    for unit, value in generated_values.items():
        result = get_norm(generated_units, "DSGVO", f"{unit}:{value}")
        assert result["norm"]["unit"] == unit
        assert result["citation"]["canonical"]["norm_id"] == f"{unit}:{value}"

    child = get_norm(
        dataset=NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True), code="EGBGB", norm="art:246a/par:1"
    )
    assert child["norm"]["canonical_id"] == "egbgb/art:246a/par:1"


def test_generated_unit_rejects_malformed_structural_values(dataset):
    for norm_ref in ("container:", "container:recitals/extra", "container:recitals?", "chapter:überblick"):
        with pytest.raises(LegalTextError) as invalid:
            get_norm(dataset, "DSGVO", norm_ref)
        assert invalid.value.code == INVALID_CITATION

    with pytest.raises(LegalTextError) as invalid_legacy_value:
        get_norm(dataset, "DSGVO", "par:abc")
    assert invalid_legacy_value.value.code == INVALID_CITATION

    with pytest.raises(LegalTextError) as invalid_child:
        resolve_citation(dataset, "EGBGB", "container", "recitals", child_unit="par", child_value="1")
    assert invalid_child.value.code == INVALID_CITATION


def test_subdivision_selection(dataset):
    result = resolve_citation(dataset, "BGB", "par", "355", absatz="1", satz="1")
    assert result["selection"]["requested_path"] == "abs:1/satz:1"
    assert "Widerrufsrecht" in result["selection"]["text"]


def test_invalid_citation_and_missing_norm_are_structured(dataset):
    with pytest.raises(LegalTextError) as invalid:
        get_norm(dataset, "BGB", "§§ 3 bis 6")
    assert invalid.value.code == INVALID_CITATION
    with pytest.raises(LegalTextError) as missing:
        resolve_citation(dataset, "BGB", "par", "999")
    assert missing.value.code == NORM_NOT_FOUND
