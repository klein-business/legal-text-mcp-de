# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from deployment.ratelimit_middleware import RateLimitMiddleware


@pytest.fixture
def app():
    a = FastAPI()
    a.add_middleware(RateLimitMiddleware, per_minute=3, per_day=5)

    @a.get("/")
    def root():
        return {"ok": True}

    return a


def test_ratelimit_allows_under_threshold(app):
    client = TestClient(app)
    for _ in range(3):
        assert client.get("/").status_code == 200


def test_ratelimit_rejects_over_per_minute(app):
    client = TestClient(app)
    for _ in range(3):
        client.get("/")
    r = client.get("/")
    assert r.status_code == 429
    assert "rate limit" in r.json()["error"]
