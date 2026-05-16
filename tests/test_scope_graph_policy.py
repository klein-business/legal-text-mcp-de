# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

from copy import deepcopy

from legal_text_mcp_de.legal_texts.relationships import (
    DEFAULT_PRIVACY_SCOPE_SEED_PATH,
    DEFAULT_SCOPE_POLICY_PATH,
    load_privacy_scope_seed,
    load_scope_policy,
    validate_privacy_scope_seed,
    validate_scope_policy,
)


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def test_scope_policy_record_is_metadata_only_and_points_to_fallback_seed():
    policy = load_scope_policy(DEFAULT_SCOPE_POLICY_PATH)

    assert validate_scope_policy(policy) == []
    assert policy["allowed_use"] == "manual_seed_only"
    assert policy["no_editorial_text_copied"] is True
    assert policy["fallback_seed_path"] == "mcp/legal_texts/data/privacy_scope_seed.v1.json"


def test_scope_policy_rejects_missing_policy_decision_fields():
    policy = load_scope_policy(DEFAULT_SCOPE_POLICY_PATH)
    policy.pop("allowed_use")

    errors = validate_scope_policy(policy)

    assert_has_error(errors, "scope policy missing fields ['allowed_use']")


def test_scope_policy_rejects_recursive_copied_editorial_text_fields():
    policy = load_scope_policy(DEFAULT_SCOPE_POLICY_PATH)
    policy["metadata"] = {"nested": {"editorial_text": "forbidden editorial wording"}}

    errors = validate_scope_policy(policy)

    assert_has_error(
        errors, "scope policy must not include copied/editorial text fields ['metadata.nested.editorial_text']"
    )


def test_seed_graph_policy_id_must_match_policy_record():
    policy = load_scope_policy(DEFAULT_SCOPE_POLICY_PATH)
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    seed["policy_id"] = "wrong-policy"

    errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "seed policy_id wrong-policy does not match scope policy")


def test_seed_graph_rejects_automated_scope_without_policy_approval():
    policy = load_scope_policy(DEFAULT_SCOPE_POLICY_PATH)
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    seed["source_basis"] = "approved_metadata"

    errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "approved_metadata seeds require automated_metadata_allowed policy")


def test_seed_graph_rejects_recursive_copied_editorial_text_fields():
    policy = load_scope_policy(DEFAULT_SCOPE_POLICY_PATH)
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    seed["relationships"][0]["metadata"]["copied_text"] = "forbidden copied wording"

    errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "seed graph must not include copied/editorial text fields")


def test_seed_graph_requires_fallback_path_when_manual_seed_only():
    policy = deepcopy(load_scope_policy(DEFAULT_SCOPE_POLICY_PATH))
    seed = load_privacy_scope_seed(DEFAULT_PRIVACY_SCOPE_SEED_PATH)
    policy.pop("fallback_seed_path")

    errors = validate_scope_policy(policy)
    seed_errors = validate_privacy_scope_seed(seed, policy)

    assert_has_error(errors, "manual_seed_only policy requires fallback_seed_path")
    assert_has_error(seed_errors, "manual_seed_only policy requires fallback_seed_path")
