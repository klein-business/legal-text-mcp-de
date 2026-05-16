# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .manifest import (
    SOURCE_FAMILIES,
    TERMINAL_STATES,
    VALIDATION_MODES,
    validate_corpus_manifest,
)
from .models import Readiness


REQUIRED_LAW_FIELDS = {"canonical_id", "display_code", "display_name", "source", "aliases", "norm_count"}
REQUIRED_NORM_FIELDS = {"canonical_id", "law_id", "norm_id", "unit", "value", "status", "url", "source"}
REQUIRED_SOURCE_FIELDS = {
    "source_kind",
    "source_identifier",
    "source_url",
    "retrieved_at",
    "stand_date_status",
    "content_hash",
}
GENERATED_PACKAGE_SCHEMA_VERSION = "generated-package.v1"
REQUIRED_GENERATED_PACKAGE_FIELDS = {
    "schema_version",
    "dataset_id",
    "package_id",
    "generated_at",
    "generator",
    "manifest_path",
    "readiness_path",
    "record_counts",
    "content_hashes",
    "validation_mode",
    "source_families",
}
REQUIRED_GENERATOR_FIELDS = {"name", "version"}
REQUIRED_RECORD_COUNTS = {
    "laws",
    "norms",
    "relationships",
    "source_limitations",
    "discovered_sources",
    "imported_sources",
}
GENERATED_NORM_UNITS = {"par", "art", "recital", "chapter", "section", "annex", "container"}
NUMERIC_NORM_UNITS = {"par", "art", "recital"}
STRUCTURAL_NORM_UNITS = {"chapter", "section", "annex", "container"}
NUMERIC_NORM_VALUE_RE = re.compile(r"^[0-9]+[a-z]?$")
STRUCTURAL_NORM_VALUE_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
CHILD_ART_PAR_NORM_ID_RE = re.compile(r"^art:([0-9]+[a-z]?)/par:([0-9]+[a-z]?)$")
RELATIONSHIP_TYPES = {
    "references",
    "implements",
    "amends",
    "repeals",
    "supplements",
    "same_subject_as",
    "source_scope_link",
    "limitation_for",
}
RELATIONSHIP_ENDPOINT_KINDS = {"law", "norm", "source_limitation"}
REQUIRED_SOURCE_LIMITATION_FIELDS = {
    "limitation_id",
    "source_family",
    "source_id",
    "terminal_state",
    "source_url",
    "reason",
    "details",
}
REQUIRED_RELATIONSHIP_FIELDS = {
    "relationship_id",
    "relationship_type",
    "subject",
    "object",
    "source_family",
    "source_id",
    "provenance",
}
COPIED_TEXT_FIELDS = {
    "copied_text",
    "editorial_text",
    "copied_editorial_text",
    "third_party_text",
    "html_text",
    "text",
}


def validate_dataset_package(path: Path, *, stage: str = "normalized_dataset") -> Readiness:
    if not path.exists():
        return Readiness(stage=stage, state="missing", details={"path": str(path)})
    if (path / "package.json").exists():
        errors = validate_generated_package(path, require_search_index=stage == "serving_dataset")
        if errors:
            return Readiness(stage=stage, state="invalid", details={"errors": errors, "path": str(path)})
        return Readiness(stage=stage, state="ready", details={"path": str(path)})
    laws_file = path / "laws.json"
    norms_file = path / "norms.json"
    if not laws_file.exists() or not norms_file.exists():
        return Readiness(
            stage=stage,
            state="invalid",
            details={"missing_files": [name for name in ("laws.json", "norms.json") if not (path / name).exists()]},
        )
    if stage == "serving_dataset" and not (path / "search-index.json").exists():
        return Readiness(
            stage=stage,
            state="invalid",
            details={"search_index_status": "pending"},
        )
    return Readiness(stage=stage, state="ready", details={"path": str(path)})


def validate_generated_package(path: Path, *, require_search_index: bool = False) -> list[str]:
    errors: list[str] = []
    if not path.exists():
        return [f"package path does not exist: {path}"]
    if not path.is_dir():
        return [f"package path must be a directory: {path}"]

    package, package_errors = _load_json_object(path / "package.json", "package.json")
    errors.extend(package_errors)
    if package is None:
        return errors

    errors.extend(_validate_package_metadata(package))
    errors.extend(_validate_package_hashes(path, package))

    laws, law_load_errors = _load_json_list(path / "laws.json", "laws.json")
    norms, norm_load_errors = _load_json_list(path / "norms.json", "norms.json")
    errors.extend(law_load_errors)
    errors.extend(norm_load_errors)
    if require_search_index and not (path / "search-index.json").exists():
        errors.append("search-index.json is required for serving_dataset")

    manifest_path = _package_relative_path(path, package.get("manifest_path"), "manifest_path", errors)
    readiness_path = _package_relative_path(path, package.get("readiness_path"), "readiness_path", errors)
    manifest: dict[str, Any] | None = None
    if manifest_path:
        manifest, manifest_load_errors = _load_json_object(manifest_path, "manifest.json")
        errors.extend(manifest_load_errors)
        if manifest is not None:
            validation_mode = package.get("validation_mode")
            terminal_required = validation_mode == "terminal" if validation_mode in VALIDATION_MODES else None
            errors.extend(f"manifest.json: {error}" for error in validate_corpus_manifest(
                manifest,
                require_terminal_states=terminal_required,
            ))
            if validation_mode in VALIDATION_MODES and manifest.get("validation_mode") != validation_mode:
                errors.append(
                    f"manifest.json validation_mode {manifest.get('validation_mode')} "
                    f"does not match package validation_mode {validation_mode}"
                )
    if readiness_path:
        readiness, readiness_load_errors = _load_json_object(readiness_path, "readiness.json")
        errors.extend(readiness_load_errors)
        if readiness is not None:
            errors.extend(_validate_readiness(readiness))

    source_limitations_path = path / "source-limitations.json"
    if source_limitations_path.exists():
        source_limitations, source_limitation_load_errors = _load_json_list(source_limitations_path, "source-limitations.json")
    else:
        source_limitations = []
        source_limitation_load_errors = []
    errors.extend(source_limitation_load_errors)
    errors.extend(_validate_generated_source_limitations(source_limitations))

    relationships_path = path / "relationships.json"
    if relationships_path.exists():
        relationships, relationship_load_errors = _load_json_list(relationships_path, "relationships.json")
    else:
        relationships = []
        relationship_load_errors = []
    errors.extend(relationship_load_errors)

    if laws is not None:
        errors.extend(validate_laws(laws))
    if norms is not None:
        errors.extend(validate_norms(norms, require_generated_container_schema=True))
    errors.extend(_validate_package_counts(package.get("record_counts"), laws, norms, relationships, source_limitations, manifest))
    errors.extend(_validate_law_norm_consistency(laws, norms))
    errors.extend(_validate_manifest_record_references(manifest, laws, norms))
    errors.extend(_validate_source_limitations_match_manifest(source_limitations, manifest))
    errors.extend(_validate_relationships(relationships, laws, norms, source_limitations, manifest))
    return errors


def validate_laws(laws: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for law in laws:
        missing = REQUIRED_LAW_FIELDS - set(law)
        if missing:
            errors.append(f"{law.get('canonical_id', '<unknown>')}: missing law fields {sorted(missing)}")
        law_id = law.get("canonical_id")
        if law_id in seen:
            errors.append(f"{law_id}: duplicate law ID")
        seen.add(law_id)
        errors.extend(_validate_source(law.get("source", {}), law_id or "<unknown>"))
    return errors


def validate_norms(norms: list[dict[str, Any]], *, require_generated_container_schema: bool = False) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for norm in norms:
        missing = REQUIRED_NORM_FIELDS - set(norm)
        if missing:
            errors.append(f"{norm.get('canonical_id', '<unknown>')}: missing norm fields {sorted(missing)}")
        canonical_id = norm.get("canonical_id")
        if canonical_id in seen:
            errors.append(f"{canonical_id}: duplicate norm ID")
        seen.add(canonical_id)
        unit = norm.get("unit")
        if unit not in GENERATED_NORM_UNITS:
            errors.append(f"{canonical_id}: unsupported norm unit {unit}")
        else:
            errors.extend(_validate_norm_id_and_value(norm))
        if require_generated_container_schema:
            if unit == "container" and norm.get("status") != "container":
                errors.append(f"{canonical_id}: container unit requires container status")
            if unit != "container" and norm.get("status") == "container":
                errors.append(f"{canonical_id}: container status requires container unit")
            if unit == "container" and norm.get("text"):
                errors.append(f"{canonical_id}: container unit must not include text")
        norm_id = norm.get("norm_id")
        law_id = norm.get("law_id")
        if isinstance(canonical_id, str) and isinstance(law_id, str) and isinstance(norm_id, str):
            expected = f"{law_id}/{norm_id}"
            if canonical_id != expected:
                errors.append(f"{canonical_id}: canonical_id must equal {expected}")
        if norm.get("status") not in {"container"} and not norm.get("text"):
            errors.append(f"{canonical_id}: active norm requires text")
        if not str(norm.get("url", "")).startswith("https://"):
            errors.append(f"{canonical_id}: URL must be HTTPS")
        errors.extend(_validate_source(norm.get("source", {}), canonical_id or "<unknown>"))
    return errors


def _validate_norm_id_and_value(norm: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    canonical_id = norm.get("canonical_id", "<unknown>")
    unit = norm.get("unit")
    value = norm.get("value")
    norm_id = norm.get("norm_id")

    if isinstance(canonical_id, str) and canonical_id != canonical_id.lower():
        errors.append(f"{canonical_id}: canonical_id must be canonical lowercase")

    if not isinstance(value, str):
        errors.append(f"{canonical_id}: norm value must be a string")
        return errors
    if value != value.lower():
        errors.append(f"{canonical_id}: value must be canonical lowercase")
    if unit in NUMERIC_NORM_UNITS and not NUMERIC_NORM_VALUE_RE.match(value):
        errors.append(f"{canonical_id}: {unit} value must match ^[0-9]+[a-z]?$")
    if unit in STRUCTURAL_NORM_UNITS and not STRUCTURAL_NORM_VALUE_RE.match(value):
        errors.append(f"{canonical_id}: {unit} value must match ^[a-z0-9][a-z0-9_-]*$")

    if not isinstance(norm_id, str):
        errors.append(f"{canonical_id}: norm_id must be a string")
        return errors
    if norm_id != norm_id.lower():
        errors.append(f"{canonical_id}: norm_id must be canonical lowercase")

    expected = f"{unit}:{value}"
    if norm_id == expected:
        return errors

    if unit == "container" and NUMERIC_NORM_VALUE_RE.match(value) and norm_id == f"art:{value}":
        return errors

    child_match = CHILD_ART_PAR_NORM_ID_RE.match(norm_id)
    if child_match and unit == "par" and value == child_match.group(2):
        return errors

    errors.append(f"{canonical_id}: norm_id must equal {expected}")
    return errors


def _validate_source(source: dict[str, Any], owner: str) -> list[str]:
    missing = REQUIRED_SOURCE_FIELDS - set(source)
    if missing:
        return [f"{owner}: missing source fields {sorted(missing)}"]
    if source.get("source_kind") == "eur-lex-cellar":
        metadata = source.get("source_metadata") or {}
        required = {"celex", "cellar_work", "expression", "language", "document"}
        missing_meta = required - set(metadata)
        if missing_meta:
            return [f"{owner}: missing EUR-Lex metadata {sorted(missing_meta)}"]
    if source.get("source_kind") == "gesetze-im-internet":
        metadata = source.get("source_metadata") or {}
        if "source_path" not in metadata:
            return [f"{owner}: missing GII source_path"]
    if source.get("source_kind") == "state-law":
        metadata = source.get("source_metadata") or {}
        required = {"state_code", "jurisdiction", "official_source_url", "source_format", "adapter_class"}
        missing_meta = required - set(metadata)
        if missing_meta:
            return [f"{owner}: missing state-law metadata {sorted(missing_meta)}"]
    return []


def _load_json_object(path: Path, label: str) -> tuple[dict[str, Any] | None, list[str]]:
    data, errors = _load_json(path, label)
    if errors:
        return None, errors
    if not isinstance(data, dict):
        return None, [f"{label} must be an object"]
    return data, []


def _load_json_list(path: Path, label: str) -> tuple[list[dict[str, Any]] | None, list[str]]:
    data, errors = _load_json(path, label)
    if errors:
        return None, errors
    if not isinstance(data, list):
        return None, [f"{label} must be a list"]
    object_errors = [f"{label}[{index}] must be an object" for index, item in enumerate(data) if not isinstance(item, dict)]
    if object_errors:
        return None, object_errors
    return data, []


def _load_json(path: Path, label: str) -> tuple[Any, list[str]]:
    if not path.exists():
        return None, [f"{label} is missing"]
    if not path.is_file():
        return None, [f"{label} must be a file"]
    try:
        return json.loads(path.read_text(encoding="utf-8")), []
    except json.JSONDecodeError as exc:
        return None, [f"{label} is invalid JSON: {exc.msg}"]


def _validate_package_metadata(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_GENERATED_PACKAGE_FIELDS - set(package)
    if missing:
        errors.append(f"package.json missing fields {sorted(missing)}")
    if package.get("schema_version") != GENERATED_PACKAGE_SCHEMA_VERSION:
        errors.append(f"package.json schema_version must be {GENERATED_PACKAGE_SCHEMA_VERSION}")
    generator = package.get("generator")
    if not isinstance(generator, dict):
        errors.append("package.json generator must be an object")
    else:
        generator_missing = REQUIRED_GENERATOR_FIELDS - set(generator)
        if generator_missing:
            errors.append(f"package.json generator missing fields {sorted(generator_missing)}")
    record_counts = package.get("record_counts")
    if not isinstance(record_counts, dict):
        errors.append("package.json record_counts must be an object")
    else:
        missing_counts = REQUIRED_RECORD_COUNTS - set(record_counts)
        if missing_counts:
            errors.append(f"package.json record_counts missing fields {sorted(missing_counts)}")
        for key, value in record_counts.items():
            if not isinstance(value, int) or value < 0:
                errors.append(f"package.json record_counts.{key} must be a non-negative integer")
    if not isinstance(package.get("content_hashes"), dict):
        errors.append("package.json content_hashes must be an object")
    if package.get("validation_mode") not in VALIDATION_MODES:
        errors.append(f"package.json validation_mode must be one of {list(VALIDATION_MODES)}")
    source_families = package.get("source_families")
    if not isinstance(source_families, list) or not all(isinstance(item, str) for item in source_families):
        errors.append("package.json source_families must be a list of strings")
    else:
        for family in source_families:
            if family not in SOURCE_FAMILIES:
                errors.append(f"package.json source_families contains unsupported source_family {family}")
    for string_field in ("dataset_id", "package_id", "generated_at", "manifest_path", "readiness_path"):
        if string_field in package and not _non_empty_string(package[string_field]):
            errors.append(f"package.json {string_field} must be a non-empty string")
    return errors


def _validate_package_hashes(path: Path, package: dict[str, Any]) -> list[str]:
    hashes = package.get("content_hashes")
    if not isinstance(hashes, dict):
        return []
    errors: list[str] = []
    expected_hashes = set(hashes)
    required_files = {"laws.json", "norms.json"}
    for package_path_field in ("manifest_path", "readiness_path"):
        value = package.get(package_path_field)
        if isinstance(value, str):
            required_files.add(value)
    for relative_path in sorted(required_files):
        if relative_path not in expected_hashes:
            errors.append(f"content_hashes missing required package file {relative_path}")
    for relative_path in ("relationships.json", "source-limitations.json", "search-index.json"):
        if (path / relative_path).exists() and relative_path not in expected_hashes:
            errors.append(f"content_hashes missing present optional package file {relative_path}")
    for relative_path, expected in hashes.items():
        if relative_path == "package.json":
            errors.append("content_hashes must not include package.json")
            continue
        if not isinstance(relative_path, str) or not isinstance(expected, str):
            errors.append("content_hashes keys and values must be strings")
            continue
        file_path = _safe_package_path(path, relative_path)
        if file_path is None:
            errors.append(f"content_hashes.{relative_path} must be a package-relative file path")
            continue
        if not file_path.exists():
            errors.append(f"content_hashes.{relative_path} references missing file")
            continue
        if not file_path.is_file():
            errors.append(f"content_hashes.{relative_path} must reference a file")
            continue
        digest = hashlib.sha256(file_path.read_bytes()).hexdigest()
        actual = f"sha256:{digest}"
        if expected != actual:
            errors.append(f"content_hashes.{relative_path} does not match file contents")
    return errors


def _package_relative_path(path: Path, value: Any, field: str, errors: list[str]) -> Path | None:
    if not isinstance(value, str):
        return None
    file_path = _safe_package_path(path, value)
    if file_path is None:
        errors.append(f"package.json {field} must be a package-relative file path")
        return None
    return file_path


def _safe_package_path(path: Path, relative_path: str) -> Path | None:
    candidate = path / relative_path
    try:
        candidate.resolve().relative_to(path.resolve())
    except ValueError:
        return None
    return candidate


def _validate_readiness(readiness: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = {"stage", "state", "details"} - set(readiness)
    if missing:
        errors.append(f"readiness.json missing fields {sorted(missing)}")
    if readiness.get("stage") not in {"normalized_dataset", "serving_dataset"}:
        errors.append("readiness.json stage must be one of ['normalized_dataset', 'serving_dataset']")
    if readiness.get("state") not in {"ready", "missing", "invalid", "source_unavailable"}:
        errors.append("readiness.json state must be one of ['ready', 'missing', 'invalid', 'source_unavailable']")
    if "details" in readiness and not isinstance(readiness["details"], dict):
        errors.append("readiness.json details must be an object")
    return errors


def _validate_package_counts(
    counts: Any,
    laws: list[dict[str, Any]] | None,
    norms: list[dict[str, Any]] | None,
    relationships: list[dict[str, Any]] | None,
    source_limitations: list[dict[str, Any]] | None,
    manifest: dict[str, Any] | None,
) -> list[str]:
    if not isinstance(counts, dict):
        return []
    actual_counts: dict[str, int] = {}
    if laws is not None:
        actual_counts["laws"] = len(laws)
    if norms is not None:
        actual_counts["norms"] = len(norms)
    if relationships is not None:
        actual_counts["relationships"] = len(relationships)
    if source_limitations is not None:
        actual_counts["source_limitations"] = len(source_limitations)
    if manifest:
        discovered_sources = manifest.get("discovered_sources")
        if isinstance(discovered_sources, list):
            actual_counts["discovered_sources"] = len(discovered_sources)
            actual_counts["imported_sources"] = sum(
                1 for source in discovered_sources if isinstance(source, dict) and source.get("terminal_state") == "imported"
            )
    errors: list[str] = []
    for key, actual in actual_counts.items():
        expected = counts.get(key)
        if isinstance(expected, int) and expected != actual:
            errors.append(f"record_counts.{key}={expected} does not match actual count {actual}")
    return errors


def _validate_law_norm_consistency(
    laws: list[dict[str, Any]] | None,
    norms: list[dict[str, Any]] | None,
) -> list[str]:
    if laws is None or norms is None:
        return []
    law_ids = {law.get("canonical_id") for law in laws}
    counts: dict[str, int] = {}
    errors: list[str] = []
    for norm in norms:
        law_id = norm.get("law_id")
        if law_id not in law_ids:
            errors.append(f"{norm.get('canonical_id', '<unknown>')}: law_id {law_id} not found in laws.json")
        if isinstance(law_id, str):
            counts[law_id] = counts.get(law_id, 0) + 1
    for law in laws:
        law_id = law.get("canonical_id")
        expected = law.get("norm_count")
        actual = counts.get(law_id, 0)
        if isinstance(expected, int) and expected != actual:
            errors.append(f"{law_id}: norm_count={expected} does not match actual norm count {actual}")
    return errors


def _validate_manifest_record_references(
    manifest: dict[str, Any] | None,
    laws: list[dict[str, Any]] | None,
    norms: list[dict[str, Any]] | None,
) -> list[str]:
    if not manifest or laws is None or norms is None:
        return []
    law_ids = {law.get("canonical_id") for law in laws}
    norm_ids = {norm.get("canonical_id") for norm in norms}
    imported_law_ids: set[Any] = set()
    imported_norm_ids: set[Any] = set()
    errors: list[str] = []
    for source in manifest.get("discovered_sources", []):
        if not isinstance(source, dict) or source.get("terminal_state") != "imported":
            continue
        for law_id in source.get("generated_law_ids") or []:
            imported_law_ids.add(law_id)
            if law_id not in law_ids:
                errors.append(f"manifest imported generated_law_id {law_id} not found in laws.json")
        for norm_id in source.get("generated_norm_ids") or []:
            imported_norm_ids.add(norm_id)
            if norm_id not in norm_ids:
                errors.append(f"manifest imported generated_norm_id {norm_id} not found in norms.json")
    for law_id in sorted(law_ids - imported_law_ids, key=str):
        errors.append(f"laws.json contains extra law {law_id} not declared by imported manifest sources")
    for norm_id in sorted(norm_ids - imported_norm_ids, key=str):
        errors.append(f"norms.json contains extra norm {norm_id} not declared by imported manifest sources")
    return errors


def _validate_source_limitations_match_manifest(
    limitations: list[dict[str, Any]] | None,
    manifest: dict[str, Any] | None,
) -> list[str]:
    if limitations is None or not manifest:
        return []
    manifest_limitations = [
        limitation
        for limitation in manifest.get("source_limitations", [])
        if isinstance(limitation, dict)
    ]
    manifest_by_limitation_id = {
        limitation.get("limitation_id"): limitation
        for limitation in manifest_limitations
        if isinstance(limitation.get("limitation_id"), str)
    }
    manifest_source_keys = {
        (limitation.get("source_family"), limitation.get("source_id"))
        for limitation in manifest_limitations
        if limitation.get("source_family") and limitation.get("source_id")
    }
    errors: list[str] = []
    for index, limitation in enumerate(limitations):
        owner = str(limitation.get("limitation_id") or f"source-limitations.json[{index}]")
        limitation_id = limitation.get("limitation_id")
        source_key = (limitation.get("source_family"), limitation.get("source_id"))
        manifest_limitation = manifest_by_limitation_id.get(limitation_id)
        if manifest_by_limitation_id:
            if manifest_limitation is None:
                errors.append(f"{owner}: source limitation is not declared by manifest source_limitations")
        elif source_key not in manifest_source_keys:
            errors.append(f"{owner}: source limitation is not declared by manifest source_limitations")
        if manifest_limitation is not None:
            errors.extend(_validate_source_limitation_matches_manifest_record(owner, limitation, manifest_limitation))
    return errors


def _validate_source_limitation_matches_manifest_record(
    owner: str,
    limitation: dict[str, Any],
    manifest_limitation: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    for field in ("source_family", "source_id", "terminal_state", "source_url", "retrieved_at", "decided_at"):
        if field not in limitation or field not in manifest_limitation:
            continue
        if limitation[field] != manifest_limitation[field]:
            errors.append(
                f"{owner}: source limitation {field} {limitation[field]} "
                f"does not match manifest {field} {manifest_limitation[field]}"
            )
    return errors


def _validate_generated_source_limitations(limitations: list[dict[str, Any]] | None) -> list[str]:
    if limitations is None:
        return []
    errors: list[str] = []
    seen: set[str] = set()
    for index, limitation in enumerate(limitations):
        owner = str(limitation.get("limitation_id") or f"source-limitations.json[{index}]")
        missing = REQUIRED_SOURCE_LIMITATION_FIELDS - set(limitation)
        if missing:
            errors.append(f"{owner}: source limitation missing fields {sorted(missing)}")
        limitation_id = limitation.get("limitation_id")
        if isinstance(limitation_id, str):
            if limitation_id in seen:
                errors.append(f"duplicate limitation_id {limitation_id}")
            seen.add(limitation_id)
        if "retrieved_at" not in limitation and "decided_at" not in limitation:
            errors.append(f"{owner}: source limitation requires retrieved_at or decided_at")
        if limitation.get("source_family") not in SOURCE_FAMILIES:
            errors.append(f"{owner}: unsupported source_family {limitation.get('source_family')}")
        if limitation.get("terminal_state") not in TERMINAL_STATES:
            errors.append(f"{owner}: unsupported terminal_state {limitation.get('terminal_state')}")
        if limitation.get("terminal_state") == "imported":
            errors.append(f"{owner}: source limitation terminal_state must not be imported")
        if "details" in limitation and not isinstance(limitation["details"], dict):
            errors.append(f"{owner}: details must be an object")
    return errors


def _validate_relationships(
    relationships: list[dict[str, Any]] | None,
    laws: list[dict[str, Any]] | None,
    norms: list[dict[str, Any]] | None,
    source_limitations: list[dict[str, Any]] | None,
    manifest: dict[str, Any] | None,
) -> list[str]:
    if relationships is None:
        return []
    law_ids = {law.get("canonical_id") for law in laws or []}
    norm_ids = {norm.get("canonical_id") for norm in norms or []}
    limitation_ids = {item.get("limitation_id") for item in source_limitations or []}
    manifest_relationship_sources = _manifest_relationship_source_keys(manifest)
    errors: list[str] = []
    seen: set[str] = set()
    for index, relationship in enumerate(relationships):
        owner = str(relationship.get("relationship_id") or f"relationships.json[{index}]")
        missing = REQUIRED_RELATIONSHIP_FIELDS - set(relationship)
        if missing:
            errors.append(f"{owner}: missing relationship fields {sorted(missing)}")
        relationship_id = relationship.get("relationship_id")
        if isinstance(relationship_id, str):
            if relationship_id in seen:
                errors.append(f"duplicate relationship_id {relationship_id}")
            seen.add(relationship_id)
        if relationship.get("relationship_type") not in RELATIONSHIP_TYPES:
            errors.append(f"{owner}: unsupported relationship_type {relationship.get('relationship_type')}")
        if relationship.get("source_family") not in SOURCE_FAMILIES:
            errors.append(f"{owner}: unsupported source_family {relationship.get('source_family')}")
        source_key = (relationship.get("source_family"), relationship.get("source_id"))
        if manifest_relationship_sources is not None and source_key not in manifest_relationship_sources:
            errors.append(f"{owner}: relationship source {source_key} is not declared by manifest relationship_sources")
        forbidden = _find_forbidden_field_paths(relationship)
        if forbidden:
            errors.append(f"{owner}: relationship must not include copied/editorial text fields {forbidden}")
        provenance = relationship.get("provenance")
        if isinstance(provenance, dict):
            provenance_missing = {"basis", "source_url"} - set(provenance)
            if provenance_missing:
                errors.append(f"{owner}: provenance missing fields {sorted(provenance_missing)}")
        elif "provenance" in relationship:
            errors.append(f"{owner}: provenance must be an object")
        for endpoint_name in ("subject", "object"):
            errors.extend(_validate_relationship_endpoint(
                owner,
                endpoint_name,
                relationship.get(endpoint_name),
                law_ids,
                norm_ids,
                limitation_ids,
            ))
    return errors


def _manifest_relationship_source_keys(manifest: dict[str, Any] | None) -> set[tuple[Any, Any]] | None:
    if not manifest:
        return None
    relationship_sources = manifest.get("relationship_sources")
    if not isinstance(relationship_sources, list):
        return set()
    return {
        (source.get("source_family"), source.get("source_id"))
        for source in relationship_sources
        if isinstance(source, dict)
    }


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


def _validate_relationship_endpoint(
    owner: str,
    endpoint_name: str,
    endpoint: Any,
    law_ids: set[Any],
    norm_ids: set[Any],
    limitation_ids: set[Any],
) -> list[str]:
    if not isinstance(endpoint, dict):
        return [f"{owner}: {endpoint_name} must be an object"]
    missing = {"kind", "id"} - set(endpoint)
    if missing:
        return [f"{owner}: {endpoint_name} missing fields {sorted(missing)}"]
    kind = endpoint.get("kind")
    target_id = endpoint.get("id")
    if kind not in RELATIONSHIP_ENDPOINT_KINDS:
        return [f"{owner}: {endpoint_name} target kind {kind} is not supported"]
    targets = {
        "law": law_ids,
        "norm": norm_ids,
        "source_limitation": limitation_ids,
    }[kind]
    if target_id not in targets:
        return [f"{owner}: {endpoint_name} target {kind}:{target_id} does not resolve"]
    return []


def _non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
