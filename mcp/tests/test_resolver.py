from pathlib import Path

import pytest

from legal_texts.dataset import NormalizedDataset
from legal_texts.errors import INVALID_CITATION, NORM_NOT_FOUND, LegalTextError
from legal_texts.resolver import get_norm, resolve_citation


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"


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


def test_get_norm_parses_encoded_canonical_child(dataset):
    result = get_norm(dataset, "egbgb", "art:246a/par:1")
    assert result["citation"]["label"] == "EGBGB Art. 246a § 1"


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
