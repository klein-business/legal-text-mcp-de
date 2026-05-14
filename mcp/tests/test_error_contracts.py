from pathlib import Path

from fastapi.testclient import TestClient

from http_api import create_http_app
from legal_texts.dataset import NormalizedDataset
from legal_texts.errors import (
    AMBIGUOUS_LAW_ALIAS,
    DATASET_NOT_READY,
    INVALID_CITATION,
    INVALID_QUERY,
    LAW_NOT_FOUND,
    NORM_NOT_FOUND,
    LegalTextError,
    ambiguous_law_alias,
    dataset_not_ready,
)
from legal_texts.registry import LawRegistry
from legal_texts.runtime import LegalTextRuntime


DATASET = Path(__file__).parent / "fixtures" / "normalized"


def test_service_and_http_error_shapes():
    dataset = NormalizedDataset.load(DATASET, require_search_index=True)
    client = TestClient(create_http_app(LegalTextRuntime.from_dataset(dataset)))
    cases = [
        (client.get("/laws/nope"), 404, LAW_NOT_FOUND),
        (client.get("/laws/bgb/norms/par%3A999"), 404, NORM_NOT_FOUND),
        (client.get("/laws/bgb/norms/%C2%A7%C2%A7%203%20bis%206"), 422, INVALID_CITATION),
        (client.get("/search", params={"query": "!!!"}), 422, INVALID_QUERY),
    ]
    for response, status, code in cases:
        assert response.status_code == status
        body = response.json()
        assert body["error"]["code"] == code
        assert "details" in body["error"]


def test_dataset_not_ready_and_ambiguous_error_shape():
    assert dataset_not_ready("missing").to_dict()["error"]["code"] == DATASET_NOT_READY
    entries = [
        {"canonical_id": "a", "display_code": "A", "display_name": "A", "source_kind": "gesetze-im-internet", "source_identifier": "a", "aliases": ["X"]},
        {"canonical_id": "b", "display_code": "B", "display_name": "B", "source_kind": "gesetze-im-internet", "source_identifier": "b", "aliases": ["X"]},
    ]
    registry = LawRegistry.from_entries(entries, validate=False)
    try:
        registry.resolve_law("x")
        assert False
    except LegalTextError as exc:
        assert exc.code == AMBIGUOUS_LAW_ALIAS
        assert exc.to_dict()["error"]["suggestions"]
