# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import re
from typing import Any, Literal


CorpusSourceFamily = Literal["gii", "eur-lex-cellar", "state-law", "third-party-scope"]
TerminalState = Literal[
    "imported",
    "unsupported_format",
    "source_unavailable",
    "parse_failed",
    "excluded_by_policy",
]
ValidationMode = Literal["discovery", "terminal"]

SOURCE_FAMILIES: tuple[CorpusSourceFamily, ...] = (
    "gii",
    "eur-lex-cellar",
    "state-law",
    "third-party-scope",
)
TERMINAL_STATES: tuple[TerminalState, ...] = (
    "imported",
    "unsupported_format",
    "source_unavailable",
    "parse_failed",
    "excluded_by_policy",
)
VALIDATION_MODES: tuple[ValidationMode, ...] = ("discovery", "terminal")
SCHEMA_VERSION = "corpus-manifest.v1"

REQUIRED_ENVELOPE_FIELDS = {
    "schema_version",
    "dataset_id",
    "package_id",
    "created_at",
    "validation_mode",
    "generator",
    "parser_versions",
    "discovered_sources",
    "canonical_ids",
    "relationship_sources",
}
REQUIRED_GENERATOR_FIELDS = {"name", "version"}
REQUIRED_GENERATED_PACKAGE_FIELDS = {
    "schema_version",
    "generated_at",
    "record_counts",
    "manifest_hash",
    "package_files",
}
REQUIRED_ALIAS_MIGRATION_FIELDS = {"from_id", "to_id", "reason", "effective_from"}
REQUIRED_CANONICAL_ID_FIELDS = {"canonical_id", "source_family", "source_id"}
REQUIRED_RELATIONSHIP_SOURCE_FIELDS = {
    "relationship_source_id",
    "source_family",
    "source_id",
    "allowed_use",
}
RELATIONSHIP_LAW_ID_FIELDS = {
    "law_id",
    "law_ids",
    "canonical_id",
    "generated_law_id",
    "generated_law_ids",
}
COPIED_TEXT_FIELDS = {
    "copied_text",
    "editorial_text",
    "copied_editorial_text",
    "third_party_text",
    "html_text",
    "text",
}


def validate_corpus_manifest(manifest: dict, *, require_terminal_states: bool | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(manifest, dict):
        return ["manifest must be an object"]

    errors.extend(_validate_envelope(manifest))
    validation_mode = manifest.get("validation_mode")
    terminal_required = validation_mode == "terminal"
    if require_terminal_states is not None and validation_mode in VALIDATION_MODES:
        if require_terminal_states != terminal_required:
            errors.append(
                f"validation_mode {validation_mode} conflicts with require_terminal_states={require_terminal_states}"
            )
    if require_terminal_states is not None:
        terminal_required = require_terminal_states

    errors.extend(_validate_discovered_sources(manifest.get("discovered_sources"), terminal_required))
    errors.extend(_validate_canonical_ids(manifest.get("canonical_ids")))
    errors.extend(_validate_relationship_sources(manifest.get("relationship_sources")))
    errors.extend(_validate_alias_migrations(manifest.get("alias_migrations")))
    errors.extend(_validate_generated_package(manifest.get("generated_package")))
    errors.extend(_validate_source_limitations(manifest.get("source_limitations")))
    return errors


def _validate_envelope(manifest: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_ENVELOPE_FIELDS - set(manifest)
    if missing:
        errors.append(f"missing top-level fields {sorted(missing)}")
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if manifest.get("validation_mode") not in VALIDATION_MODES:
        errors.append(f"validation_mode must be one of {list(VALIDATION_MODES)}")

    generator = manifest.get("generator")
    if not isinstance(generator, dict):
        errors.append("generator must be an object")
    else:
        generator_missing = REQUIRED_GENERATOR_FIELDS - set(generator)
        if generator_missing:
            errors.append(f"generator missing fields {sorted(generator_missing)}")

    for field in ("parser_versions",):
        if field in manifest and not isinstance(manifest[field], dict):
            errors.append(f"{field} must be an object")
    for field in ("discovered_sources", "canonical_ids", "relationship_sources"):
        if field in manifest and not isinstance(manifest[field], list):
            errors.append(f"{field} must be a list")
    return errors


def _validate_discovered_sources(sources: Any, require_terminal_states: bool) -> list[str]:
    if sources is None:
        return []
    if not isinstance(sources, list):
        return []

    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            errors.append(f"discovered_sources[{index}] must be an object")
            continue
        owner = _owner(source, f"discovered_sources[{index}]")
        source_family = source.get("source_family")
        source_id = source.get("source_id")
        if not source_family:
            errors.append(f"{owner}: missing source_family")
        elif source_family not in SOURCE_FAMILIES:
            errors.append(f"{owner}: unsupported source_family {source_family}")
        if not source_id:
            errors.append(f"{owner}: missing source_id")
        key = (source_family, source_id)
        if source_family and source_id:
            if key in seen:
                errors.append(f"duplicate discovered_sources source key {key}")
            seen.add(key)
        errors.extend(_validate_source_family_provenance(source, owner))
        errors.extend(_validate_terminal_state(source, owner, require_terminal_states))
    return errors


def _validate_source_limitations(limitations: Any) -> list[str]:
    if limitations is None:
        return []
    if not isinstance(limitations, list):
        return ["source_limitations must be a list"]

    errors: list[str] = []
    seen: set[tuple[str, str]] = set()
    for index, limitation in enumerate(limitations):
        if not isinstance(limitation, dict):
            errors.append(f"source_limitations[{index}] must be an object")
            continue
        owner = _owner(limitation, f"source_limitations[{index}]")
        source_family = limitation.get("source_family")
        source_id = limitation.get("source_id")
        if not source_family:
            errors.append(f"{owner}: missing source_family")
        elif source_family not in SOURCE_FAMILIES:
            errors.append(f"{owner}: unsupported source_family {source_family}")
        if not source_id:
            errors.append(f"{owner}: missing source_id")
        key = (source_family, source_id)
        if source_family and source_id:
            if key in seen:
                errors.append(f"duplicate source_limitations source key {key}")
            seen.add(key)
        errors.extend(_validate_source_family_provenance(limitation, owner))
        errors.extend(_validate_terminal_state(limitation, owner, True))
    return errors


def _validate_terminal_state(record: dict[str, Any], owner: str, require_terminal_states: bool) -> list[str]:
    errors: list[str] = []
    terminal_state = record.get("terminal_state")
    if not terminal_state:
        if require_terminal_states:
            errors.append(f"{owner}: missing terminal_state")
        return errors
    if terminal_state not in TERMINAL_STATES:
        return [f"{owner}: unsupported terminal_state {terminal_state}"]

    if terminal_state == "imported":
        errors.extend(
            _require_fields(
                record,
                owner,
                "imported",
                (
                    "canonical_id",
                    "source_url",
                    "content_sha256",
                    "retrieved_at",
                    "parser_version",
                ),
            )
        )
        if not record.get("generated_law_ids") and not record.get("generated_norm_ids"):
            errors.append(f"{owner}: imported requires at least one generated law or norm ID")
    elif terminal_state == "unsupported_format":
        errors.extend(_require_fields(record, owner, "unsupported_format", ("source_url", "retrieved_at", "reason")))
        if not record.get("content_type") and not record.get("format_hint"):
            errors.append(f"{owner}: unsupported_format requires content_type or format_hint")
    elif terminal_state == "source_unavailable":
        errors.extend(_require_fields(record, owner, "source_unavailable", ("source_url", "retrieved_at", "retryable")))
        if "http_status" not in record and "error_code" not in record:
            errors.append(f"{owner}: source_unavailable requires http_status or error_code")
    elif terminal_state == "parse_failed":
        errors.extend(_require_fields(record, owner, "parse_failed", ("source_url", "retrieved_at", "parser_version")))
        if record.get("content_fetched") is True and not record.get("content_sha256"):
            errors.append(f"{owner}: parse_failed requires content_sha256 when content was fetched")
        if not _any_text(record, ("diagnostic", "diagnostic_text", "error", "error_message")):
            errors.append(f"{owner}: parse_failed requires diagnostic text")
    elif terminal_state == "excluded_by_policy":
        errors.extend(
            _require_fields(
                record,
                owner,
                "excluded_by_policy",
                (
                    "policy_reason",
                    "policy_reference",
                    "decided_at",
                ),
            )
        )
        forbidden = sorted(COPIED_TEXT_FIELDS & set(record))
        if forbidden:
            errors.append(f"{owner}: excluded_by_policy must not include copied/editorial text fields {forbidden}")
    return errors


def _validate_source_family_provenance(record: dict[str, Any], owner: str) -> list[str]:
    source_family = record.get("source_family")
    if source_family == "gii":
        return _validate_gii_provenance(record, owner)
    if source_family == "eur-lex-cellar":
        return _validate_eurlex_provenance(record, owner)
    if source_family == "state-law":
        return _validate_state_law_provenance(record, owner)
    if source_family == "third-party-scope":
        return _validate_third_party_scope_provenance(record, owner)
    return []


def _validate_gii_provenance(record: dict[str, Any], owner: str) -> list[str]:
    errors = _require_metadata_fields(record, owner, "gii", ("source_path", "index_url", "xml_zip_url", "toc_url"))
    source_path = _field(record, "source_path")
    source_id = record.get("source_id")
    if source_path and source_id != f"gii:{source_path}":
        errors.append(f"{owner}: gii source_id must equal gii:<source_path>")
    if not _field(record, "toc_sha256") and not _field(record, "discovery_artifact_id"):
        errors.append(f"{owner}: gii requires toc_sha256 or discovery_artifact_id")
    return errors


def _validate_eurlex_provenance(record: dict[str, Any], owner: str) -> list[str]:
    errors = _require_metadata_fields(record, owner, "eur-lex-cellar", ("celex", "language"))
    language = _field(record, "language")
    if language and language != "de":
        errors.append(f"{owner}: eur-lex-cellar language must be de")
    if (
        not _field(record, "cellar_uri")
        and not _field(record, "official_eurlex_url")
        and not _official_eurlex_source(record)
    ):
        errors.append(f"{owner}: eur-lex-cellar requires cellar_uri or official EUR-Lex URL")
    for field_group, message in (
        (("work", "cellar_work"), "work"),
        (("expression", "cellar_expression"), "expression"),
        (("document", "cellar_document"), "document"),
        (("version_policy", "consolidation_policy"), "consolidation/version policy"),
    ):
        if not any(_field(record, field) for field in field_group):
            errors.append(f"{owner}: eur-lex-cellar requires {message}")
    return errors


def _validate_state_law_provenance(record: dict[str, Any], owner: str) -> list[str]:
    return _require_metadata_fields(
        record,
        owner,
        "state-law",
        ("state_code", "jurisdiction", "official_source_url", "source_format", "adapter_class"),
    )


def _validate_third_party_scope_provenance(record: dict[str, Any], owner: str) -> list[str]:
    errors = _require_metadata_fields(
        record,
        owner,
        "third-party-scope",
        (
            "provider",
            "source_url",
            "robots_reviewed_at",
            "terms_reviewed_at",
            "policy_review_reference",
            "allowed_use",
        ),
    )
    if not _field(record, "target_official_record") and not _field(record, "source_limitation_id"):
        errors.append(f"{owner}: third-party-scope requires target official record or source limitation provenance")
    if _field(record, "no_editorial_text_copied") is not True:
        errors.append(f"{owner}: third-party-scope requires no_editorial_text_copied=true")
    forbidden = sorted(COPIED_TEXT_FIELDS & set(record))
    if forbidden:
        errors.append(f"{owner}: third-party-scope must not include copied/editorial text fields {forbidden}")
    return errors


def _validate_canonical_ids(canonical_ids: Any) -> list[str]:
    if canonical_ids is None:
        return []
    if not isinstance(canonical_ids, list):
        return ["canonical_ids must be a list"]

    errors: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(canonical_ids):
        if not isinstance(record, dict):
            errors.append(f"canonical_ids[{index}] must be an object")
            continue
        owner = record.get("canonical_id") or f"canonical_ids[{index}]"
        missing = REQUIRED_CANONICAL_ID_FIELDS - set(record)
        if missing:
            errors.append(f"{owner}: canonical_id record missing fields {sorted(missing)}")
        canonical_id = record.get("canonical_id")
        if canonical_id:
            if canonical_id in seen:
                errors.append(f"duplicate canonical_id {canonical_id}")
            seen.add(canonical_id)
        source_family = record.get("source_family")
        source_id = record.get("source_id")
        if source_family and source_family not in SOURCE_FAMILIES:
            errors.append(f"{owner}: unsupported source_family {source_family}")
        if source_family == "third-party-scope":
            errors.append(f"{owner}: third-party-scope cannot create legal-text canonical IDs")
        if source_family == "eur-lex-cellar":
            celex = record.get("celex")
            if celex and source_id and not source_id.endswith(str(celex)):
                errors.append(f"{owner}: CELEX {celex} does not match source_id {source_id}")
            celex_fragment = _celex_canonical_fragment(celex)
            if canonical_id and celex_fragment and celex_fragment not in canonical_id:
                errors.append(f"{owner}: canonical_id {canonical_id} does not match CELEX {celex}")
        if source_family == "state-law":
            state_code = record.get("state_code")
            if not state_code:
                errors.append(f"{owner}: state-law canonical_id record requires state_code")
            elif canonical_id and not canonical_id.startswith(f"state:{state_code}/"):
                errors.append(f"{owner}: state-law canonical_id must start with state:{state_code}/")
    return errors


def _validate_relationship_sources(relationship_sources: Any) -> list[str]:
    if relationship_sources is None:
        return []
    if not isinstance(relationship_sources, list):
        return ["relationship_sources must be a list"]

    errors: list[str] = []
    seen: set[str] = set()
    for index, record in enumerate(relationship_sources):
        if not isinstance(record, dict):
            errors.append(f"relationship_sources[{index}] must be an object")
            continue
        owner = record.get("relationship_source_id") or f"relationship_sources[{index}]"
        missing = REQUIRED_RELATIONSHIP_SOURCE_FIELDS - set(record)
        if missing:
            errors.append(f"{owner}: relationship_source missing fields {sorted(missing)}")
        relationship_source_id = record.get("relationship_source_id")
        if relationship_source_id:
            if relationship_source_id in seen:
                errors.append(f"duplicate relationship_source_id {relationship_source_id}")
            seen.add(relationship_source_id)
        if RELATIONSHIP_LAW_ID_FIELDS & set(record):
            errors.append(f"{owner}: relationship source must not create legal-text law IDs")
        forbidden = _find_forbidden_field_paths(record)
        if forbidden:
            errors.append(f"{owner}: relationship source must not include copied/editorial text fields {forbidden}")
        errors.extend(_validate_source_family_provenance(record, owner))
    return errors


def _validate_alias_migrations(alias_migrations: Any) -> list[str]:
    if alias_migrations is None:
        return []
    if not isinstance(alias_migrations, list):
        return ["alias_migrations must be a list"]

    errors: list[str] = []
    for index, migration in enumerate(alias_migrations):
        if not isinstance(migration, dict):
            errors.append(f"alias_migrations[{index}] must be an object")
            continue
        missing = REQUIRED_ALIAS_MIGRATION_FIELDS - set(migration)
        if missing:
            errors.append(f"alias_migrations[{index}] missing fields {sorted(missing)}")
    return errors


def _validate_generated_package(generated_package: Any) -> list[str]:
    if generated_package is None:
        return []
    if not isinstance(generated_package, dict):
        return ["generated_package must be an object"]
    missing = REQUIRED_GENERATED_PACKAGE_FIELDS - set(generated_package)
    if missing:
        return [f"generated_package missing fields {sorted(missing)}"]
    return []


def _require_fields(
    record: dict[str, Any],
    owner: str,
    state: str,
    fields: tuple[str, ...],
) -> list[str]:
    return [f"{owner}: {state} requires {field}" for field in fields if field not in record]


def _require_metadata_fields(
    record: dict[str, Any],
    owner: str,
    family: str,
    fields: tuple[str, ...],
) -> list[str]:
    return [f"{owner}: {family} requires {field}" for field in fields if _field(record, field) is None]


def _field(record: dict[str, Any], name: str) -> Any:
    if name in record:
        return record[name]
    metadata = record.get("source_metadata")
    if isinstance(metadata, dict):
        return metadata.get(name)
    return None


def _any_text(record: dict[str, Any], fields: tuple[str, ...]) -> bool:
    return any(isinstance(record.get(field), str) and record[field].strip() for field in fields)


def _find_forbidden_field_paths(value: Any, prefix: str = "") -> list[str]:
    paths: list[str] = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_path = f"{prefix}.{key}" if prefix else str(key)
            if key in COPIED_TEXT_FIELDS:
                paths.append(key_path)
            paths.extend(_find_forbidden_field_paths(child, key_path))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            item_path = f"{prefix}[{index}]" if prefix else f"[{index}]"
            paths.extend(_find_forbidden_field_paths(item, item_path))
    return sorted(paths)


def _official_eurlex_source(record: dict[str, Any]) -> bool:
    source_url = _field(record, "source_url")
    return isinstance(source_url, str) and source_url.startswith("https://eur-lex.europa.eu/")


def _celex_canonical_fragment(celex: Any) -> str | None:
    if not isinstance(celex, str):
        return None
    match = re.fullmatch(r"3(\d{4})[A-Z](\d{4})", celex)
    if not match:
        return None
    year, sequence = match.groups()
    return f"{year}_{int(sequence)}"


def _owner(record: dict[str, Any], fallback: str) -> str:
    value = record.get("source_id") or record.get("relationship_source_id")
    return str(value) if value else fallback
