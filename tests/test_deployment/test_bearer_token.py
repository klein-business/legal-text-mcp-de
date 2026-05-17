# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from deployment.bearer_token import validate_bearer


def test_validate_bearer_returns_none_for_missing_header():
    assert validate_bearer(None) is None
    assert validate_bearer("") is None


def test_validate_bearer_rejects_unknown_token(monkeypatch):
    monkeypatch.setenv("HOSTED_BEARER_TOKENS", "good-token-1,good-token-2")
    assert validate_bearer("Bearer unknown") is None


def test_validate_bearer_accepts_known_token(monkeypatch):
    monkeypatch.setenv("HOSTED_BEARER_TOKENS", "good-token-1,good-token-2")
    assert validate_bearer("Bearer good-token-1") == "good-token-1"
    assert validate_bearer("bearer good-token-2") == "good-token-2"
