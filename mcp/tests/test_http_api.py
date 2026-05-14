from pathlib import Path

from fastapi.testclient import TestClient

from http_api import create_http_app
from legal_texts.dataset import NormalizedDataset
from legal_texts.runtime import LegalTextRuntime


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"


def client():
    dataset = NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True)
    return TestClient(create_http_app(LegalTextRuntime.from_dataset(dataset)))


def test_health_and_ready():
    c = client()
    assert c.get("/health").json() == {"status": "ok"}
    ready = c.get("/ready")
    assert ready.status_code == 200
    assert ready.json()["stage"] == "serving_dataset"


def test_law_endpoints():
    c = client()
    laws = c.get("/laws?query=DSGVO").json()
    assert laws["count"] == 1
    law = c.get("/laws/BGB").json()
    assert law["law"]["canonical_id"] == "bgb"
    assert law["norms"]


def test_norm_endpoint_supports_encoded_child_path():
    c = client()
    container = c.get("/laws/egbgb/norms/art%3A246a")
    child = c.get("/laws/egbgb/norms/art%3A246a%2Fpar%3A1")
    assert container.status_code == 200
    assert container.json()["norm"]["status"] == "container"
    assert child.status_code == 200
    assert child.json()["norm"]["canonical_id"] == "egbgb/art:246a/par:1"


def test_search_endpoint_and_errors():
    c = client()
    result = c.get("/search", params=[("query", "Werbung"), ("codes", "UWG")])
    assert result.status_code == 200
    assert result.json()["codes"] == ["uwg_2004"]
    invalid = c.get("/search", params={"query": "!!!"})
    assert invalid.status_code == 422
    assert invalid.json()["error"]["code"] == "INVALID_QUERY"


def test_openapi_contains_phase1_paths_and_schemas():
    schema = client().get("/openapi.json").json()
    for path in ["/health", "/ready", "/laws", "/laws/{code}", "/laws/{code}/norms/{norm}", "/search"]:
        assert path in schema["paths"]
    assert schema["components"]["schemas"]
