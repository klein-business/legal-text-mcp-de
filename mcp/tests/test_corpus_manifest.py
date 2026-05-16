# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import json
from pathlib import Path

from legal_texts.manifest import (
    SOURCE_FAMILIES,
    TERMINAL_STATES,
    validate_corpus_manifest,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "manifest"


def load_manifest(name: str) -> dict:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def test_manifest_constants_define_phase_one_vocabularies():
    assert SOURCE_FAMILIES == ("gii", "eur-lex-cellar", "state-law", "third-party-scope")
    assert TERMINAL_STATES == (
        "imported",
        "unsupported_format",
        "source_unavailable",
        "parse_failed",
        "excluded_by_policy",
    )


def test_valid_terminal_manifest_passes_with_default_and_explicit_mode():
    manifest = load_manifest("valid_terminal.json")

    assert validate_corpus_manifest(manifest) == []
    assert validate_corpus_manifest(manifest, require_terminal_states=True) == []


def test_valid_discovery_manifest_allows_unfetched_sources():
    manifest = load_manifest("valid_discovery.json")

    assert validate_corpus_manifest(manifest) == []
    assert validate_corpus_manifest(manifest, require_terminal_states=False) == []


def test_require_terminal_states_conflicts_with_manifest_mode():
    discovery_errors = validate_corpus_manifest(load_manifest("valid_discovery.json"), require_terminal_states=True)
    terminal_errors = validate_corpus_manifest(load_manifest("valid_terminal.json"), require_terminal_states=False)

    assert_has_error(discovery_errors, "validation_mode discovery conflicts with require_terminal_states=True")
    assert_has_error(terminal_errors, "validation_mode terminal conflicts with require_terminal_states=False")


def test_manifest_envelope_fields_are_required():
    errors = validate_corpus_manifest(load_manifest("invalid_missing_envelope.json"))

    assert_has_error(errors, "missing top-level fields ['package_id']")
    assert_has_error(errors, "generator missing fields ['version']")


def test_duplicate_source_family_and_source_id_are_rejected():
    errors = validate_corpus_manifest(load_manifest("invalid_duplicate_source.json"))

    assert_has_error(errors, "duplicate discovered_sources source key ('gii', 'gii:bdsg')")


def test_terminal_state_required_fields_are_validated():
    errors = validate_corpus_manifest(load_manifest("invalid_terminal_fields.json"))

    assert_has_error(errors, "gii:imported-missing: imported requires canonical_id")
    assert_has_error(errors, "gii:imported-missing: imported requires at least one generated law or norm ID")
    assert_has_error(errors, "gii:unsupported-missing: unsupported_format requires content_type or format_hint")
    assert_has_error(errors, "gii:unsupported-missing: unsupported_format requires reason")
    assert_has_error(errors, "state-law:be/unavailable-missing: source_unavailable requires http_status or error_code")
    assert_has_error(errors, "state-law:be/unavailable-missing: source_unavailable requires retryable")
    assert_has_error(errors, "gii:parse-failed-missing: parse_failed requires content_sha256 when content was fetched")
    assert_has_error(errors, "gii:parse-failed-missing: parse_failed requires diagnostic text")
    assert_has_error(errors, "third-party-scope:excluded-missing: excluded_by_policy requires policy_reference")
    assert_has_error(errors, "third-party-scope:excluded-missing: excluded_by_policy requires decided_at")
    assert_has_error(errors, "third-party-scope:excluded-missing: excluded_by_policy must not include copied/editorial text fields")


def test_canonical_ids_alias_migrations_and_state_law_prefix_are_validated():
    errors = validate_corpus_manifest(load_manifest("invalid_canonical_policy.json"))

    assert_has_error(errors, "duplicate canonical_id dsgvo_eu_2016_679")
    assert_has_error(errors, "dsgvo_eu_2016_679: CELEX 32024R1689 does not match source_id eur-lex-cellar:32016R0679")
    assert_has_error(errors, "dsgvo_eu_2016_679: canonical_id dsgvo_eu_2016_679 does not match CELEX 32024R1689")
    assert_has_error(errors, "bln-dsg: state-law canonical_id must start with state:be/")
    assert_has_error(errors, "state:/missing-state: state-law canonical_id record requires state_code")
    assert_has_error(errors, "alias_migrations[0] missing fields ['effective_from', 'reason', 'to_id']")


def test_relationship_sources_cannot_create_legal_text_law_ids():
    errors = validate_corpus_manifest(load_manifest("invalid_relationship_law_id.json"))

    assert_has_error(errors, "rel-src:bad: relationship source must not create legal-text law IDs")


def test_relationship_sources_reject_nested_copied_editorial_text_fields():
    manifest = load_manifest("valid_terminal.json")
    manifest["relationship_sources"][0]["metadata"] = {"nested": {"editorial_text": "copied text"}}

    errors = validate_corpus_manifest(manifest)

    assert_has_error(
        errors,
        "rel-src:dsgvo-gesetz-scope: relationship source must not include copied/editorial text fields ['metadata.nested.editorial_text']",
    )


def test_canonical_ids_reject_third_party_scope_sources():
    errors = validate_corpus_manifest(load_manifest("invalid_third_party_canonical_id.json"))

    assert_has_error(errors, "fake-third-party-law: third-party-scope cannot create legal-text canonical IDs")


def test_source_limitations_reuse_terminal_state_and_provenance_validation():
    errors = validate_corpus_manifest(load_manifest("invalid_source_limitation.json"))

    assert_has_error(errors, "state-law:hh/hmbdsg: unsupported terminal_state blocked_by_portal")
    assert_has_error(errors, "state-law:hh/hmbdsg: state-law requires state_code")
    assert_has_error(errors, "state-law:hh/hmbdsg: state-law requires jurisdiction")
    assert_has_error(errors, "state-law:hh/hmbdsg: state-law requires official_source_url")
    assert_has_error(errors, "state-law:hh/hmbdsg: state-law requires source_format")
    assert_has_error(errors, "state-law:hh/hmbdsg: state-law requires adapter_class")


def test_source_limitations_require_terminal_state_in_discovery_mode():
    errors = validate_corpus_manifest(load_manifest("invalid_discovery_source_limitation_missing_terminal.json"))

    assert_has_error(errors, "state-law:hh/hmbdsg: missing terminal_state")
