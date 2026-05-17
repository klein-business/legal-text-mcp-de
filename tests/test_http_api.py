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


# --- #64 — request body size limit (defence-in-depth) ----------------------


def _client_with_limit(max_bytes: int) -> TestClient:
    """Build a TestClient with a custom max_request_body_bytes override.

    `RequestBodySizeLimitMiddleware` is constructed inside `create_http_app`
    from `settings.max_request_body_bytes`. Monkey-patching `settings` for
    a single test would leak to the rest of the suite; instead, build a
    fresh app with the limit injected at module import time via a custom
    Settings override.
    """

    from legal_text_mcp_de.config import Settings
    from legal_text_mcp_de.http_api import RequestBodySizeLimitMiddleware

    dataset = NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True)
    runtime = LegalTextRuntime.from_dataset(dataset)
    # Build the app manually so we can swap the middleware's limit
    # without touching the module-level `settings` singleton.
    from legal_text_mcp_de.http_api import create_http_app as _create

    app = _create(runtime)
    # Replace the auto-added middleware. Starlette's middleware stack
    # is rebuilt lazily on first request, so direct list edits work
    # before any request hits the app.
    app.user_middleware = [m for m in app.user_middleware if m.cls is not RequestBodySizeLimitMiddleware]
    app.add_middleware(RequestBodySizeLimitMiddleware, max_bytes=max_bytes)
    app.middleware_stack = None  # force rebuild on next request
    _ = Settings  # silence unused-import warning
    return TestClient(app)


def test_body_size_limit_small_body_passes():
    """A request well under the limit succeeds normally."""
    c = _client_with_limit(max_bytes=10_000)
    # /health is a GET with no body; should always pass irrespective of limit.
    resp = c.get("/health")
    assert resp.status_code == 200


def test_body_size_limit_exactly_at_limit_passes():
    """A request whose Content-Length equals the limit is accepted."""
    c = _client_with_limit(max_bytes=100)
    # FastAPI POSTs are not defined on the read-only API; use an arbitrary
    # endpoint that ignores the body. The middleware is path-agnostic.
    payload = b"x" * 100
    resp = c.post("/health", content=payload, headers={"content-length": "100"})
    # The endpoint returns 405 (method not allowed) — but the middleware
    # passed it through, which is what we are asserting here.
    assert resp.status_code != 413


def test_body_size_limit_over_limit_is_rejected():
    """A request whose Content-Length exceeds the limit returns 413."""
    c = _client_with_limit(max_bytes=100)
    payload = b"x" * 101
    resp = c.post("/health", content=payload, headers={"content-length": "101"})
    assert resp.status_code == 413
    body = resp.json()
    assert body["error"]["code"] == "PAYLOAD_TOO_LARGE"
    assert body["error"]["details"]["max_request_body_bytes"] == 100
    assert body["error"]["details"]["received_bytes"] == 101


def test_body_size_limit_missing_content_length_passes_through():
    """A request without Content-Length is not pre-rejected by this middleware.

    Chunked or unknown-length requests fall through to the transport layer;
    the cap remains effective at the proxy and reader level.
    """
    c = _client_with_limit(max_bytes=10)
    # GET requests in the TestClient have no Content-Length header.
    resp = c.get("/health")
    assert resp.status_code == 200


def test_body_size_limit_invalid_content_length_passes_through():
    """A malformed Content-Length header is not pre-rejected.

    Behaviour matches the framework default — invalid headers are not
    grounds for a 413 at this layer; the transport rejects them.
    """
    c = _client_with_limit(max_bytes=100)
    resp = c.post("/health", content=b"", headers={"content-length": "not-a-number"})
    assert resp.status_code != 413
