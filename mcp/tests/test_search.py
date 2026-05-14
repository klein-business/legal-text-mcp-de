from pathlib import Path

import pytest

from legal_texts.dataset import NormalizedDataset
from legal_texts.errors import INVALID_QUERY, LegalTextError
from legal_texts.search import SearchService


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"


@pytest.fixture
def search():
    return SearchService(NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True))


def test_all_law_search_contract(search):
    result = search.search_laws("Widerrufsrecht")
    assert result["count"] >= 1
    first = result["results"][0]
    assert first["score"] == 1.0
    assert first["law_id"] == "bgb"
    assert "<b>" not in first["snippet"]
    assert first["source"]["source_kind"] == "gesetze-im-internet"


def test_selected_law_search_resolves_aliases(search):
    result = search.search_laws("Werbung", ["UWG"])
    assert result["count"] >= 1
    assert {item["law_id"] for item in result["results"]} == {"uwg_2004"}
    assert result["codes"] == ["uwg_2004"]


def test_multi_token_and_semantics(search):
    result = search.search_laws("personenbezogene Daten", ["DSGVO"])
    assert result["count"] >= 1
    assert all("dsgvo" in item["law_id"] for item in result["results"])


def test_invalid_query_is_structured(search):
    with pytest.raises(LegalTextError) as exc:
        search.search_laws("!!!")
    assert exc.value.code == INVALID_QUERY


def test_scores_are_normalized_and_ordered(search):
    result = search.search_laws("Verbraucher")
    scores = [item["score"] for item in result["results"]]
    assert scores == sorted(scores, reverse=True)
    assert all(0 <= score <= 1 for score in scores)
