#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from fastapi.testclient import TestClient
from http_api import create_http_app  # type: ignore[import-not-found]
from legal_texts.dataset import NormalizedDataset  # type: ignore[import-not-found]
from legal_texts.relationships import validate_privacy_scope_seed  # type: ignore[import-not-found]
from legal_texts.runtime import LegalTextRuntime  # type: ignore[import-not-found]
from legal_texts.state_law_inventory import FIXED_STATE_CODES  # type: ignore[import-not-found]
from server import create_mcp_app  # type: ignore[import-not-found]


SCHEMA_VERSION = "full-corpus-validation-bundle.v1"
ACCEPTED_LIMITATION_STATES = {"source_unavailable", "unsupported_format", "parse_failed", "excluded_by_policy"}
REQUIRED_EU_CELEXS = {"32024R1689", "32023R2854"}
REQUIRED_BENCHMARK_DECISIONS = {
    "load": "review_dataset_loading_strategy",
    "search": "consider_external_or_persisted_search_index",
    "memory": "consider_memory_mapped_or_chunked_runtime_loading",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def load_artifact(
    path: Path, name: str, *, generated_at_fallback: str
) -> tuple[dict[str, Any], dict[str, Any] | None, list[str]]:
    if not path.exists():
        errors = [f"{name}: artifact missing at {path}"]
        return _section(name, path, "missing", None, None, {}, errors), None, errors
    if not path.is_file():
        errors = [f"{name}: artifact path is not a file: {path}"]
        return _section(name, path, "invalid", None, None, {}, errors), None, errors
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors = [f"{name}: artifact is not valid JSON: {exc}"]
        return _section(name, path, "invalid", None, sha256_file(path), {}, errors), None, errors
    if not isinstance(data, dict):
        errors = [f"{name}: artifact must be a JSON object"]
        return _section(name, path, "invalid", None, sha256_file(path), {}, errors), None, errors

    status = data.get("status") or ("invalid" if data.get("validation_errors") else "ready")
    if status in {"passed", "passed_with_migration_decisions"}:
        status = "ready"
    errors = [f"{name}: {error}" for error in data.get("validation_errors", [])]
    section = _section(
        name,
        path,
        status,
        data.get("generated_at") or data.get("retrieved_at") or data.get("maintained_at") or generated_at_fallback,
        sha256_file(path),
        summarize_artifact(data),
        errors,
        schema_version=data.get("schema_version"),
    )
    return section, data, errors


def _section(
    name: str,
    path: Path,
    status: str,
    generated_at: str | None,
    sha256: str | None,
    summary: dict[str, Any],
    errors: list[str],
    *,
    schema_version: str | None = None,
) -> dict[str, Any]:
    return {
        "status": status,
        "generated_at": generated_at,
        "source_artifact": str(path),
        "path": str(path),
        "sha256": sha256,
        "schema_version": schema_version,
        "summary": summary,
        "errors": errors,
    }


def summarize_artifact(data: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for key in (
        "counts",
        "record_counts",
        "terminal_state_counts",
        "terminal_state_coverage",
        "critical_law_outcomes",
        "validation_errors",
        "expected_counts",
        "actual_counts",
        "seeded_celex",
        "validation_status",
    ):
        if key in data:
            summary[key] = data[key]
    if "status" in data:
        summary["status"] = data["status"]
    if "migration_decisions" in data:
        summary["migration_decisions"] = data["migration_decisions"]
    return summary


def _add_section_errors(section: dict[str, Any], errors: list[str]) -> list[str]:
    section["errors"].extend(errors)
    if errors and section["status"] not in {"missing"}:
        section["status"] = "invalid"
    return errors


def _validate_schema(name: str, raw: dict[str, Any] | None, section: dict[str, Any], expected: str) -> list[str]:
    if raw is None:
        return []
    if raw.get("schema_version") != expected:
        return [f"{name}: schema_version must be {expected}"]
    return []


def validate_gii_artifact(raw: dict[str, Any] | None, section: dict[str, Any]) -> list[str]:
    if raw is None:
        return []
    errors = _validate_schema("gii", raw, section, "gii-corpus-gate.v1")
    if raw.get("validation_errors"):
        errors.extend(f"gii: {error}" for error in raw["validation_errors"])
    counts = raw.get("counts") if isinstance(raw.get("counts"), dict) else {}
    discovered = counts.get("discovered_sources")  # type: ignore[union-attr]
    imported = counts.get("imported_sources")  # type: ignore[union-attr]
    if not isinstance(discovered, int) or discovered <= 0:
        errors.append("gii: counts.discovered_sources must be positive")
    coverage = raw.get("terminal_state_coverage")
    if not isinstance(coverage, dict) or not coverage:
        errors.append("gii: missing terminal_state_coverage")
    elif (
        isinstance(discovered, int)
        and sum(value for value in coverage.values() if isinstance(value, int)) != discovered
    ):
        errors.append("gii: terminal_state_coverage must sum to discovered_sources")
    if isinstance(coverage, dict) and isinstance(imported, int) and coverage.get("imported", 0) != imported:
        errors.append("gii: imported terminal coverage must match counts.imported_sources")
    generated_package = raw.get("generated_package")
    if not isinstance(generated_package, dict):
        errors.append("gii: missing generated_package")
    else:
        if not generated_package.get("path"):
            errors.append("gii: generated_package.path is required")
        if not generated_package.get("sha256"):
            errors.append("gii: generated_package.sha256 is required")
    outcomes = raw.get("critical_law_outcomes")
    if not isinstance(outcomes, dict):
        errors.append("gii: missing critical_law_outcomes")
    else:
        if "bdsg_2018" not in outcomes:
            errors.append("gii: missing critical_law_outcomes.bdsg_2018")
        if "tdddg" not in outcomes and "ttdsg" not in outcomes:
            errors.append("gii: missing critical_law_outcomes.tdddg")
    return _add_section_errors(section, errors)


def critical_law_evidence(gii_section: dict[str, Any], gii_raw: dict[str, Any] | None) -> dict[str, Any]:
    outcomes = gii_raw.get("critical_law_outcomes") if isinstance(gii_raw, dict) else None
    errors: list[str] = []
    evidence: dict[str, Any] = {}
    if not isinstance(outcomes, dict):
        errors.append("critical_laws: GII artifact missing critical_law_outcomes")
        return {
            "status": "missing",
            "required": ["bdsg_2018", "tdddg"],
            "evidence_sections": ["gii"],
            "evidence": evidence,
            "errors": errors,
        }

    dataset = _load_gii_dataset(gii_raw, errors)
    required_aliases = {
        "bdsg_2018": ("bdsg_2018",),
        "tdddg": ("tdddg", "ttdsg"),
    }
    for canonical, aliases in required_aliases.items():
        outcome_key = next((alias for alias in aliases if alias in outcomes), None)
        outcome = outcomes.get(outcome_key) if outcome_key else None
        if not isinstance(outcome, dict):
            errors.append(f"critical_laws: missing outcome for {canonical}")
            continue
        law_evidence, law_errors = _critical_law_outcome_evidence(canonical, outcome_key, outcome, dataset)
        evidence[canonical] = law_evidence
        errors.extend(law_errors)

    return {
        "status": "ready" if not errors else "invalid",
        "required": ["bdsg_2018", "tdddg"],
        "evidence_sections": ["gii"],
        "evidence": evidence,
        "errors": errors,
    }


def _load_gii_dataset(gii_raw: dict[str, Any] | None, errors: list[str]) -> NormalizedDataset | None:
    generated_package = gii_raw.get("generated_package") if isinstance(gii_raw, dict) else None
    package_path = generated_package.get("path") if isinstance(generated_package, dict) else None
    if not package_path:
        errors.append("critical_laws: GII generated_package.path is required for resolution evidence")
        return None
    try:
        return NormalizedDataset.load(Path(package_path), require_search_index=True)
    except Exception as exc:  # noqa: BLE001 - surfaced as validation evidence.
        errors.append(f"critical_laws: failed to load GII generated package: {type(exc).__name__}: {exc}")
        return None


def _critical_law_outcome_evidence(
    canonical: str,
    outcome_key: str | None,
    outcome: dict[str, Any],
    dataset: NormalizedDataset | None,
) -> tuple[dict[str, Any], list[str]]:
    terminal_state = (
        outcome.get("terminal_state")
        or (outcome.get("manifest_record") or {}).get("terminal_state")
        or (outcome.get("limitation") or {}).get("terminal_state")
    )
    evidence: dict[str, Any] = {
        "outcome_key": outcome_key,
        "terminal_state": terminal_state,
        "status": "invalid",
        "imported": False,
        "release_blocking_limitation": False,
    }
    if terminal_state == "imported":
        errors = _validate_imported_critical_law(canonical, outcome, dataset, evidence)
    else:
        errors = _validate_limited_critical_law(canonical, outcome, evidence)
    evidence["status"] = "ready" if not errors else "invalid"
    return evidence, errors


def _validate_imported_critical_law(
    canonical: str,
    outcome: dict[str, Any],
    dataset: NormalizedDataset | None,
    evidence: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    manifest_record = outcome.get("manifest_record") if isinstance(outcome.get("manifest_record"), dict) else {}
    law = outcome.get("law") if isinstance(outcome.get("law"), dict) else {}
    if law and law.get("canonical_id") != canonical:
        errors.append(f"critical_laws: {canonical} law canonical_id must match required canonical ID")
    if manifest_record.get("source_family") != "gii":  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} imported evidence must have source_family gii")
    for field in ("source_id", "source_path", "source_url", "generated_law_ids", "generated_norm_ids"):
        if not manifest_record.get(field):  # type: ignore[union-attr]
            errors.append(f"critical_laws: {canonical} imported evidence missing {field}")
    source_url = manifest_record.get("source_url")  # type: ignore[union-attr]
    if isinstance(source_url, str) and not source_url.startswith("https://www.gesetze-im-internet.de/"):
        errors.append(f"critical_laws: {canonical} source_url must be official GII")
    source_path = manifest_record.get("source_path")  # type: ignore[union-attr]
    source_id = manifest_record.get("source_id")  # type: ignore[union-attr]
    generated_law_ids = manifest_record.get("generated_law_ids")  # type: ignore[union-attr]
    if isinstance(generated_law_ids, list):
        if canonical not in generated_law_ids:
            errors.append(f"critical_laws: {canonical} generated_law_ids must include {canonical}")
    elif generated_law_ids:
        errors.append(f"critical_laws: {canonical} generated_law_ids must be a list")
    generated_norm_ids = manifest_record.get("generated_norm_ids")  # type: ignore[union-attr]
    if isinstance(generated_norm_ids, list):
        wrong_norm_ids = [
            norm_id
            for norm_id in generated_norm_ids
            if not isinstance(norm_id, str) or not norm_id.startswith(f"{canonical}/")
        ]
        if wrong_norm_ids:
            errors.append(f"critical_laws: {canonical} generated_norm_ids must all belong to {canonical}")
    elif generated_norm_ids:
        errors.append(f"critical_laws: {canonical} generated_norm_ids must be a list")
    norm_canonical = generated_norm_ids[0] if isinstance(generated_norm_ids, list) and generated_norm_ids else None
    if dataset is not None:
        _validate_dataset_critical_source(
            canonical,
            norm_canonical,
            dataset,
            source_id=source_id,
            source_path=source_path,
            source_url=source_url,
            errors=errors,
        )
    if dataset is not None and isinstance(norm_canonical, str) and "/" in norm_canonical:
        evidence["resolution"] = _resolution_evidence(dataset, norm_canonical)
        for channel, result in evidence["resolution"].items():
            if result.get("status") != "resolved":
                errors.append(f"critical_laws: {canonical} {channel} resolution failed")
    elif dataset is not None:
        errors.append(f"critical_laws: {canonical} generated_norm_ids must contain canonical norm IDs")
    evidence["imported"] = not errors
    evidence["source_id"] = manifest_record.get("source_id")  # type: ignore[union-attr]
    return errors


def _validate_dataset_critical_source(
    canonical: str,
    norm_canonical: str | None,
    dataset: NormalizedDataset,
    *,
    source_id: Any,
    source_path: Any,
    source_url: Any,
    errors: list[str],
) -> None:
    law_record = dataset.laws_by_id.get(canonical)
    if not isinstance(law_record, dict):
        errors.append(f"critical_laws: {canonical} generated package missing law")
        return
    law_source = law_record.get("source") if isinstance(law_record.get("source"), dict) else {}
    law_metadata = law_source.get("source_metadata") if isinstance(law_source.get("source_metadata"), dict) else {}  # type: ignore[union-attr]
    if law_metadata.get("source_path") != source_path:  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} package law source_path does not match outcome")
    if law_source.get("source_url") != source_url:  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} package law source_url does not match outcome")
    if law_source.get("source_identifier") and source_path and law_source.get("source_identifier") != source_path:  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} package law source_identifier does not match outcome")
    if isinstance(source_id, str) and source_path and source_id != f"gii:{source_path}":
        errors.append(f"critical_laws: {canonical} source_id must match source_path")
    if not isinstance(norm_canonical, str):
        return
    norm_record = dataset.norms_by_canonical.get(norm_canonical)
    if not isinstance(norm_record, dict):
        errors.append(f"critical_laws: {canonical} generated package missing norm {norm_canonical}")
        return
    if norm_record.get("law_id") != canonical:
        errors.append(f"critical_laws: {canonical} resolved norm must belong to {canonical}")
    norm_source = norm_record.get("source") if isinstance(norm_record.get("source"), dict) else {}
    norm_metadata = norm_source.get("source_metadata") if isinstance(norm_source.get("source_metadata"), dict) else {}  # type: ignore[union-attr]
    if norm_metadata.get("source_path") != source_path:  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} package norm source_path does not match outcome")
    if norm_source.get("source_url") != source_url:  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} package norm source_url does not match outcome")


def _resolution_evidence(dataset: NormalizedDataset, norm_canonical: str) -> dict[str, Any]:
    law_id, norm_id = norm_canonical.split("/", 1)
    runtime = LegalTextRuntime.from_dataset(dataset)
    result: dict[str, Any] = {}
    try:
        runtime_norm = runtime.get_norm(law_id, norm_id)
        result["runtime"] = {"status": "resolved", "canonical_id": runtime_norm["norm"]["canonical_id"]}
    except Exception as exc:  # noqa: BLE001
        result["runtime"] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    try:
        app = create_mcp_app(runtime)
        mcp_norm = app._tool_manager._tools["get_norm"].fn(code=law_id, norm=norm_id)
        if isinstance(mcp_norm, dict) and mcp_norm.get("norm", {}).get("canonical_id") == norm_canonical:
            result["mcp"] = {"status": "resolved", "canonical_id": norm_canonical}
        else:
            result["mcp"] = {"status": "failed", "error": "unexpected MCP response"}
    except Exception as exc:  # noqa: BLE001
        result["mcp"] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    try:
        response = TestClient(create_http_app(runtime)).get(
            f"/laws/{quote(law_id, safe='')}/norms/{quote(norm_id, safe='')}"
        )
        if response.status_code == 200 and response.json().get("norm", {}).get("canonical_id") == norm_canonical:
            result["http"] = {"status": "resolved", "canonical_id": norm_canonical}
        else:
            result["http"] = {"status": "failed", "status_code": response.status_code}
    except Exception as exc:  # noqa: BLE001
        result["http"] = {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}
    return result


def _validate_limited_critical_law(canonical: str, outcome: dict[str, Any], evidence: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    limitation = outcome.get("limitation") if isinstance(outcome.get("limitation"), dict) else {}
    details = limitation.get("details") if isinstance(limitation.get("details"), dict) else {}  # type: ignore[union-attr]
    terminal_state = limitation.get("terminal_state") or outcome.get("terminal_state")  # type: ignore[union-attr]
    if terminal_state != "source_unavailable":
        errors.append(f"critical_laws: {canonical} limitation must use terminal_state source_unavailable")
    source_url = limitation.get("source_url") or outcome.get("source_url")  # type: ignore[union-attr]
    if not isinstance(source_url, str) or not source_url.startswith("https://www.gesetze-im-internet.de/"):
        errors.append(f"critical_laws: {canonical} limitation requires official GII source_url")
    source_id = (
        limitation.get("source_id")  # type: ignore[union-attr]
        or outcome.get("source_id")
        or (outcome.get("manifest_record") or {}).get("source_id")
    )
    source_path = (
        limitation.get("source_path")  # type: ignore[union-attr]
        or details.get("source_path")  # type: ignore[union-attr]
        or (outcome.get("manifest_record") or {}).get("source_path")
    )
    if not limitation.get("limitation_id"):  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} limitation missing limitation_id")
    if not source_id:
        errors.append(f"critical_laws: {canonical} limitation missing source_id")
    if not source_path:
        errors.append(f"critical_laws: {canonical} limitation missing source_path")
    if isinstance(source_id, str) and source_path and source_id != f"gii:{source_path}":
        errors.append(f"critical_laws: {canonical} limitation source_id must match source_path")
    if not limitation.get("reason"):  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} limitation missing reason")
    if not limitation.get("retrieved_at") and not limitation.get("decided_at"):  # type: ignore[union-attr]
        errors.append(f"critical_laws: {canonical} limitation missing retrieved_at or decided_at")
    if not _has_substantive_upstream_evidence(details):  # type: ignore[arg-type]
        errors.append(f"critical_laws: {canonical} limitation missing substantive upstream evidence details")
    release_blocking = limitation.get("release_blocking") is True or details.get("release_blocking") is True  # type: ignore[union-attr]
    if not release_blocking:
        errors.append(f"critical_laws: {canonical} limitation must be release_blocking")
    evidence["release_blocking_limitation"] = release_blocking and not errors
    evidence["source_id"] = source_id
    evidence["limitation_id"] = limitation.get("limitation_id")  # type: ignore[union-attr]
    return errors


def _has_substantive_upstream_evidence(details: dict[str, Any]) -> bool:
    http_status = details.get("http_status")
    if type(http_status) is int and http_status > 0:
        return True
    for field in ("error_code", "content_type"):
        value = details.get(field)
        if isinstance(value, str) and value.strip():
            return True
    return details.get("official_upstream_evidence") is True


def validate_dsgvo_artifact(raw: dict[str, Any] | None, section: dict[str, Any]) -> list[str]:
    if raw is None:
        return []
    errors = _validate_schema("dsgvo", raw, section, "dsgvo-full-counts.v1")
    if raw.get("validation_errors"):
        errors.extend(f"dsgvo: {error}" for error in raw["validation_errors"])
    policy = raw.get("policy") if isinstance(raw.get("policy"), dict) else {}
    selected = raw.get("selected_source") if isinstance(raw.get("selected_source"), dict) else {}
    for field in (
        "celex",
        "cellar_work",
        "expression",
        "document",
        "language",
        "version_policy",
        "consolidation_policy",
        "content_hash",
    ):
        if not policy.get(field):  # type: ignore[union-attr]
            errors.append(f"dsgvo: missing policy {field}")
        if not selected.get(field):  # type: ignore[union-attr]
            errors.append(f"dsgvo: missing selected_source {field}")
    expected = raw.get("expected_counts") if isinstance(raw.get("expected_counts"), dict) else {}
    actual = raw.get("actual_counts") if isinstance(raw.get("actual_counts"), dict) else raw.get("counts", {})
    if not isinstance(expected.get("articles"), int) or not isinstance(expected.get("recitals"), int):  # type: ignore[union-attr]
        errors.append("dsgvo: expected_counts must include articles and recitals")
    elif actual.get("articles") != expected["articles"] or actual.get("recitals") != expected["recitals"]:  # type: ignore[union-attr,index]
        errors.append("dsgvo: actual counts must equal expected_counts")
    boundary = raw.get("boundary_samples") if isinstance(raw.get("boundary_samples"), dict) else {}
    if not boundary:
        errors.append("dsgvo: missing boundary_samples")
    else:
        for key in ("articles", "recitals"):
            sample = boundary.get(key) if isinstance(boundary.get(key), dict) else {}
            if not sample.get("expected") or sample.get("missing"):  # type: ignore[union-attr]
                errors.append(f"dsgvo: boundary_samples.{key} must retain expected samples with no missing entries")
    return _add_section_errors(section, errors)


def validate_eu_neighbors_artifact(raw: dict[str, Any] | None, section: dict[str, Any]) -> list[str]:
    if raw is None:
        return []
    errors = _validate_schema("eu_neighbors", raw, section, "eu-neighbor-sources.v1")
    if raw.get("validation_errors"):
        errors.extend(f"eu_neighbors: {error}" for error in raw["validation_errors"])
    seeded = set(raw.get("seeded_celex") or [])
    if not REQUIRED_EU_CELEXS.issubset(seeded):
        errors.append("eu_neighbors: seeded_celex must include AI Act and Data Act CELEX IDs")
    results = raw.get("source_results")
    result_by_celex = {item.get("celex"): item for item in results} if isinstance(results, list) else {}
    if not seeded or set(result_by_celex) != seeded:
        errors.append("eu_neighbors: source_results must cover seeded_celex")
    for celex, result in result_by_celex.items():
        state = result.get("terminal_state")
        if state == "imported":
            for field in ("canonical_id", "source_url", "version_policy", "generated_norm_ids"):
                if not result.get(field):
                    errors.append(f"eu_neighbors: {celex} imported result missing {field}")
        elif state in ACCEPTED_LIMITATION_STATES:
            if not result.get("limitation_id") and not result.get("limitation"):
                errors.append(f"eu_neighbors: {celex} limited result missing limitation evidence")
        else:
            errors.append(f"eu_neighbors: {celex} terminal_state must be imported or limited")
    return _add_section_errors(section, errors)


def validate_state_law_artifact(raw: dict[str, Any] | None, section: dict[str, Any]) -> list[str]:
    if raw is None:
        return []
    errors = _validate_schema("state_law", raw, section, "state-law-pdf-source-gate.v1")
    if raw.get("validation_errors"):
        errors.extend(f"state_law: {error}" for error in raw["validation_errors"])
    counts = raw.get("counts") if isinstance(raw.get("counts"), dict) else {}
    if counts.get("total_states") != 16:  # type: ignore[union-attr]
        errors.append("state_law: total_states must be 16")
    if counts.get("imported", 0) + counts.get("limited", 0) != 16:  # type: ignore[union-attr]
        errors.append("state_law: imported + limited must equal 16")
    coverage_path_value = raw.get("coverage_path")
    coverage_path = Path(coverage_path_value) if isinstance(coverage_path_value, str) else None
    if coverage_path is None or not coverage_path.is_file():
        errors.append("state_law: coverage_path must exist")
        return _add_section_errors(section, errors)
    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"state_law: coverage_path is invalid JSON: {exc}")
        return _add_section_errors(section, errors)
    if coverage.get("schema_version") != "state-law-coverage.v1":
        errors.append("state_law: coverage schema_version must be state-law-coverage.v1")
    states = coverage.get("states")
    if not isinstance(states, list) or len(states) != 16:
        errors.append("state_law: coverage must contain 16 states")
    else:
        seen_state_codes: set[str] = set()
        for entry in states:
            state = entry.get("terminal_state") if isinstance(entry, dict) else None
            state_code = entry.get("state_code") if isinstance(entry, dict) else "unknown"
            if isinstance(state_code, str):
                if state_code in seen_state_codes:
                    errors.append(f"state_law: duplicate coverage state {state_code}")
                seen_state_codes.add(state_code)
            if state == "imported":
                if not entry.get("law_id"):
                    errors.append(f"state_law: {state_code} imported state missing law_id")
            elif state in ACCEPTED_LIMITATION_STATES:
                if not entry.get("source_limitation_id"):
                    errors.append(f"state_law: {state_code} limited state missing source_limitation_id")
            else:
                errors.append(f"state_law: {state_code} terminal_state must be imported or limited")
        missing = sorted(set(FIXED_STATE_CODES) - seen_state_codes)
        unknown = sorted(seen_state_codes - set(FIXED_STATE_CODES))
        if missing:
            errors.append(f"state_law: missing coverage states {missing}")
        if unknown:
            errors.append(f"state_law: unknown coverage states {unknown}")
    return _add_section_errors(section, errors)


def validate_relationships_artifact(raw: dict[str, Any] | None, section: dict[str, Any]) -> list[str]:
    if raw is None:
        return []
    errors = _validate_schema("relationships", raw, section, "privacy-scope-seed.v1")
    relationship_source = raw.get("relationship_source")
    if not isinstance(relationship_source, dict):
        errors.append("relationships: relationship_source must be an object")
    if not raw.get("relationships") and not raw.get("source_limitations"):
        errors.append("relationships: relationships or source_limitations must be nonempty")
    policy = _policy_from_seed(raw)
    seed_errors = validate_privacy_scope_seed(raw, policy)
    if seed_errors:
        errors.extend(f"relationships: {error}" for error in seed_errors)
    section["summary"]["validation_status"] = "ready" if not errors else "invalid"
    section["summary"]["validation_errors"] = errors
    return _add_section_errors(section, errors)


def _policy_from_seed(seed: dict[str, Any]) -> dict[str, Any]:
    relationship_source = seed.get("relationship_source") if isinstance(seed.get("relationship_source"), dict) else {}
    return {
        "schema_version": "dsgvo-scope-policy.v1",
        "policy_id": seed.get("policy_id"),
        "source_url": relationship_source.get("source_url", "https://dsgvo-gesetz.de/"),  # type: ignore[union-attr]
        "reviewed_at": seed.get("maintained_at"),
        "robots_reviewed_at": relationship_source.get("robots_reviewed_at"),  # type: ignore[union-attr]
        "robots_result": "reviewed",
        "terms_reviewed_at": relationship_source.get("terms_reviewed_at"),  # type: ignore[union-attr]
        "terms_result": "reviewed",
        "allowed_use": relationship_source.get("allowed_use"),  # type: ignore[union-attr]
        "no_editorial_text_copied": relationship_source.get("no_editorial_text_copied"),  # type: ignore[union-attr]
        "fallback_seed_path": "privacy_scope_seed.v1.json",
    }


def validate_benchmark_artifact(raw: dict[str, Any] | None, section: dict[str, Any]) -> list[str]:
    if raw is None:
        return []
    errors = _validate_schema("benchmark", raw, section, "corpus-runtime-benchmark.v1")
    if raw.get("validation_errors"):
        errors.extend(f"benchmark: {error}" for error in raw["validation_errors"])
    if raw.get("status") not in {"passed", "passed_with_migration_decisions"}:
        errors.append("benchmark: status must be passed or passed_with_migration_decisions")
    errors.extend(_benchmark_decision_errors(raw))
    return _add_section_errors(section, errors)


def _benchmark_decision_errors(raw: dict[str, Any]) -> list[str]:
    thresholds = raw.get("thresholds") if isinstance(raw.get("thresholds"), dict) else {}
    decisions = {item.get("decision") for item in raw.get("migration_decisions", []) if isinstance(item, dict)}
    errors: list[str] = []
    if (
        raw.get("load_time_ms", 0) > thresholds.get("max_load_ms", float("inf"))  # type: ignore[union-attr]
        and REQUIRED_BENCHMARK_DECISIONS["load"] not in decisions
    ):
        errors.append("benchmark: missing load migration decision")
    search = raw.get("sampled_search") if isinstance(raw.get("sampled_search"), dict) else {}
    if (
        search.get("p95_ms", 0) > thresholds.get("max_search_p95_ms", float("inf"))  # type: ignore[union-attr]
        and REQUIRED_BENCHMARK_DECISIONS["search"] not in decisions
    ):
        errors.append("benchmark: missing search migration decision")
    memory = raw.get("combined_memory_mb", raw.get("estimated_memory_mb", 0))
    if (
        memory > thresholds.get("max_memory_mb", float("inf"))  # type: ignore[union-attr]
        and REQUIRED_BENCHMARK_DECISIONS["memory"] not in decisions
    ):
        errors.append("benchmark: missing memory migration decision")
    return errors


def build_bundle(
    *,
    gii_artifact: Path,
    dsgvo_artifact: Path,
    eu_neighbors_artifact: Path,
    state_law_artifact: Path,
    relationships_artifact: Path,
    benchmark_artifact: Path,
) -> tuple[dict[str, Any], int]:
    sections: dict[str, dict[str, Any]] = {}
    raws: dict[str, dict[str, Any] | None] = {}
    validation_errors: list[str] = []
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    for name, path in {
        "gii": gii_artifact,
        "dsgvo": dsgvo_artifact,
        "eu_neighbors": eu_neighbors_artifact,
        "state_law": state_law_artifact,
        "relationships": relationships_artifact,
        "benchmark": benchmark_artifact,
    }.items():
        section, raw, errors = load_artifact(path, name, generated_at_fallback=created_at)
        sections[name] = section
        raws[name] = raw
        validation_errors.extend(errors)

    validation_errors.extend(validate_gii_artifact(raws["gii"], sections["gii"]))
    validation_errors.extend(validate_dsgvo_artifact(raws["dsgvo"], sections["dsgvo"]))
    validation_errors.extend(validate_eu_neighbors_artifact(raws["eu_neighbors"], sections["eu_neighbors"]))
    validation_errors.extend(validate_state_law_artifact(raws["state_law"], sections["state_law"]))
    validation_errors.extend(validate_relationships_artifact(raws["relationships"], sections["relationships"]))
    validation_errors.extend(validate_benchmark_artifact(raws["benchmark"], sections["benchmark"]))

    critical_laws = critical_law_evidence(sections["gii"], raws["gii"])
    validation_errors.extend(critical_laws["errors"])

    benchmark_raw = raws["benchmark"] or {}
    benchmark_status = (
        benchmark_raw.get("status") or sections["benchmark"]["summary"].get("status") or sections["benchmark"]["status"]
    )
    migration_decisions = benchmark_raw.get("migration_decisions", [])
    runtime_ready = sections["benchmark"]["status"] == "ready" and benchmark_status in {
        "passed",
        "passed_with_migration_decisions",
    }

    bundle = {
        "schema_version": SCHEMA_VERSION,
        "created_at": created_at,
        "gii": sections["gii"],
        "dsgvo": sections["dsgvo"],
        "critical_laws": critical_laws,
        "eu_neighbors": sections["eu_neighbors"],
        "state_law": sections["state_law"],
        "relationships": sections["relationships"],
        "runtime_readiness": {
            "status": "ready" if runtime_ready else "invalid",
            "benchmark_status": benchmark_status,
            "benchmark_artifact": str(benchmark_artifact),
        },
        "benchmark": sections["benchmark"],
        "migration_decisions": migration_decisions,
        "validation_errors": validation_errors,
    }

    if bundle["runtime_readiness"]["status"] != "ready":
        validation_errors.append("runtime_readiness: benchmark is not ready")
    if bundle["critical_laws"]["status"] != "ready":
        validation_errors.append("critical_laws: required GII evidence is not ready")

    return bundle, 1 if validation_errors else 0


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose opt-in full-corpus validation bundle evidence.")
    parser.add_argument("--gii-artifact", required=True, type=Path)
    parser.add_argument("--dsgvo-artifact", required=True, type=Path)
    parser.add_argument("--eu-neighbors-artifact", required=True, type=Path)
    parser.add_argument("--state-law-artifact", required=True, type=Path)
    parser.add_argument("--relationships-artifact", required=True, type=Path)
    parser.add_argument("--benchmark-artifact", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    bundle, exit_code = build_bundle(
        gii_artifact=args.gii_artifact,
        dsgvo_artifact=args.dsgvo_artifact,
        eu_neighbors_artifact=args.eu_neighbors_artifact,
        state_law_artifact=args.state_law_artifact,
        relationships_artifact=args.relationships_artifact,
        benchmark_artifact=args.benchmark_artifact,
    )
    write_json(args.output, bundle)
    if exit_code:
        for error in bundle["validation_errors"]:
            print(error, file=sys.stderr)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
