# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path

from fastapi.testclient import TestClient

from legal_text_mcp_de.http_api import create_http_app
from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"
GENERATED_PACKAGE = Path(__file__).parent / "fixtures" / "generated_package"


def client(path: Path = FIXTURE_DATASET):
    dataset = NormalizedDataset.load(path, require_search_index=True)
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


def test_corpus_runtime_endpoints_support_legacy_and_generated_packages():
    legacy = client().get("/corpus/coverage")
    assert legacy.status_code == 200
    assert legacy.json()["generated_package_present"] is False
    assert legacy.json()["counts"]["relationships"] == 0

    generated = client(GENERATED_PACKAGE)
    coverage = generated.get("/corpus/coverage")
    assert coverage.status_code == 200
    assert coverage.json()["generated_package_present"] is True
    assert coverage.json()["counts"]["source_limitations"] == 1

    limitations = generated.get(
        "/corpus/source-limitations",
        params={"source_family": "state-law", "terminal_state": "source_unavailable"},
    )
    assert limitations.status_code == 200
    assert limitations.json()["count"] == 1

    relationships = generated.get("/laws/DSGVO/norms/art%3A5/relationships")
    assert relationships.status_code == 200
    assert relationships.json()["count"] == 1
    assert relationships.json()["relationships"][0]["target"]["kind"] == "source_limitation"


def test_openapi_contains_supported_paths_and_schemas():
    schema = client().get("/openapi.json").json()
    for path in [
        "/health",
        "/ready",
        "/laws",
        "/laws/{code}",
        "/laws/{code}/norms/{norm}",
        "/laws/{code}/norms/{norm}/relationships",
        "/corpus/coverage",
        "/corpus/source-limitations",
        "/search",
    ]:
        assert path in schema["paths"]
    assert schema["components"]["schemas"]
