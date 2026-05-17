# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import json
import logging

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from deployment.anonymised_logging import AnonymisedLoggingMiddleware


def test_anonymised_logging_emits_one_line_per_request(caplog):
    a = FastAPI()
    a.add_middleware(AnonymisedLoggingMiddleware)

    @a.get("/")
    def root():
        return {"ok": True}

    with caplog.at_level(logging.INFO, logger="legal_text_mcp_de.hosted"):
        client = TestClient(a)
        client.get("/foo")
    log_lines = [r.message for r in caplog.records if r.name == "legal_text_mcp_de.hosted"]
    assert len(log_lines) == 1
    parsed = json.loads(log_lines[0])
    assert parsed["method"] == "GET"
    assert parsed["path"] == "/foo"
    assert "status" in parsed
    assert "latency_ms" in parsed
    # Crucially: no body or full UA stored
    assert "body" not in parsed
    assert "user_agent" not in parsed
