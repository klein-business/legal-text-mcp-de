# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree.ElementTree import ParseError

from .gii_xml import parse_gii_zip
from .importer import sha256_bytes
from .manifest import validate_corpus_manifest
from .sources import SOURCE_SPECS
from .validation import validate_generated_package, validate_laws, validate_norms


GII_CORPUS_GATE_SCHEMA_VERSION = "gii-corpus-gate.v1"
GII_BULK_GENERATOR_VERSION = "gii-bulk-fixture.v1"
CRITICAL_GII_LAWS = {
    "bdsg_2018": "bdsg_2018",
    "ttdsg": "tdddg",
}
CRITICAL_GII_SOURCE_PATHS = set(CRITICAL_GII_LAWS)


@dataclass
class GiiBulkResult:
    package_dir: Path
    laws: list[dict[str, Any]]
    norms: list[dict[str, Any]]
    manifest: dict[str, Any]
    source_limitations: list[dict[str, Any]]
    terminal_state_counts: dict[str, int]
    source_outcomes: dict[str, dict[str, Any]]
    validation_errors: list[str]


def run_gii_bulk_normalization(
    discovery_artifact: dict[str, Any],
    *,
    payload_dir: Path,
    package_dir: Path,
    retrieved_at: str,
    upstream_limitations: list[dict[str, Any]] | None = None,
) -> GiiBulkResult:
    records = _discovered_records(discovery_artifact)
    upstream_limitations_by_source_path = _upstream_limitations_by_source_path(upstream_limitations or [])
    package_dir.mkdir(parents=True, exist_ok=True)
    laws: list[dict[str, Any]] = []
    norms: list[dict[str, Any]] = []
    discovered_sources: list[dict[str, Any]] = []
    source_limitations: list[dict[str, Any]] = []
    source_outcomes: dict[str, dict[str, Any]] = {}
    terminal_state_counts = {
        "imported": 0,
        "source_unavailable": 0,
        "unsupported_format": 0,
        "parse_failed": 0,
    }

    for record in records:
        outcome = _normalize_source(
            record,
            payload_dir=payload_dir,
            retrieved_at=retrieved_at,
            upstream_limitation=upstream_limitations_by_source_path.get(record["source_path"]),
        )
        source_outcomes[record["source_path"]] = outcome
        terminal_state_counts[outcome["terminal_state"]] += 1
        discovered_sources.append(outcome["manifest_record"])
        if outcome["law"] is not None:
            laws.append(outcome["law"])
            norms.extend(outcome["norms"])
        if outcome["limitation"] is not None:
            source_limitations.append(outcome["limitation"])

    manifest = _build_manifest(discovery_artifact, discovered_sources, source_limitations, retrieved_at)
    _write_generated_package(
        package_dir=package_dir,
        laws=sorted(laws, key=lambda item: item["canonical_id"]),
        norms=sorted(norms, key=lambda item: item["canonical_id"]),
        manifest=manifest,
        source_limitations=sorted(source_limitations, key=lambda item: item["limitation_id"]),
        retrieved_at=retrieved_at,
        discovered_count=len(records),
        imported_count=terminal_state_counts["imported"],
    )
    validation_errors = (
        validate_laws(laws)
        + validate_norms(norms, require_generated_container_schema=True)
        + [f"manifest: {error}" for error in validate_corpus_manifest(manifest, require_terminal_states=True)]
        + [f"package: {error}" for error in validate_generated_package(package_dir, require_search_index=True)]
    )
    result = GiiBulkResult(
        package_dir=package_dir,
        laws=laws,
        norms=norms,
        manifest=manifest,
        source_limitations=source_limitations,
        terminal_state_counts={key: value for key, value in terminal_state_counts.items() if value},
        source_outcomes=source_outcomes,
        validation_errors=validation_errors,
    )
    validation_errors.extend(critical_law_gate_errors(result))
    return result


def critical_law_gate_errors(result: GiiBulkResult) -> list[str]:
    law_ids = {law["canonical_id"] for law in result.laws}
    norm_law_ids = {norm["law_id"] for norm in result.norms}
    errors: list[str] = []
    for source_path, canonical_id in sorted(CRITICAL_GII_LAWS.items()):
        outcome = result.source_outcomes.get(source_path)
        if outcome is None:
            errors.append(f"critical law {source_path} missing terminal state")
            continue
        state = outcome["terminal_state"]
        if state == "imported":
            if canonical_id not in law_ids or canonical_id not in norm_law_ids:
                errors.append(f"critical law {source_path} imported but canonical {canonical_id} is not resolvable")
            continue
        if state == "source_unavailable" and _is_release_blocking_upstream_limitation(outcome.get("limitation")):
            continue
        errors.append(f"critical law {source_path} has forbidden terminal_state {state}")
    return errors


def build_gii_corpus_gate_artifact(
    discovery_artifact: dict[str, Any],
    *,
    payload_dir: Path,
    package_dir: Path,
    retrieved_at: str,
    parser_variant_matrix_path: Path | None = None,
    upstream_limitations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    result = run_gii_bulk_normalization(
        discovery_artifact,
        payload_dir=payload_dir,
        package_dir=package_dir,
        retrieved_at=retrieved_at,
        upstream_limitations=upstream_limitations,
    )
    package_hash = _hash_package(package_dir)
    return {
        "schema_version": GII_CORPUS_GATE_SCHEMA_VERSION,
        "generated_at": retrieved_at,
        "counts": {
            "discovered_sources": sum(result.terminal_state_counts.values()),
            "imported_sources": result.terminal_state_counts.get("imported", 0),
            "source_unavailable": result.terminal_state_counts.get("source_unavailable", 0),
            "unsupported_format": result.terminal_state_counts.get("unsupported_format", 0),
            "parse_failed": result.terminal_state_counts.get("parse_failed", 0),
            "laws": len(result.laws),
            "norms": len(result.norms),
            "source_limitations": len(result.source_limitations),
        },
        "terminal_state_coverage": result.terminal_state_counts,
        "critical_law_outcomes": {
            source_path: result.source_outcomes.get(source_path, {"terminal_state": "missing"})
            for source_path in sorted(CRITICAL_GII_SOURCE_PATHS)
        },
        "generated_package": {
            "path": str(package_dir),
            "sha256": package_hash,
        },
        "parser_variant_matrix": _parser_variant_matrix(parser_variant_matrix_path),
        "validation_errors": result.validation_errors,
    }


def write_gii_corpus_gate_artifact(artifact: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _normalize_source(
    record: dict[str, Any],
    *,
    payload_dir: Path,
    retrieved_at: str,
    upstream_limitation: dict[str, Any] | None,
) -> dict[str, Any]:
    source_path = record["source_path"]
    canonical_id = _canonical_id_for_source_path(source_path)
    zip_path = payload_dir / f"{source_path}.zip"
    unsupported_path = payload_dir / f"{source_path}.txt"
    base_manifest = _base_manifest_source(record)
    if not zip_path.exists():
        if unsupported_path.exists():
            body = unsupported_path.read_bytes()
            limitation = _source_limitation(
                record,
                "unsupported_format",
                retrieved_at,
                reason="reachable payload is not an XML ZIP",
                content_sha256=sha256_bytes(body),
                content_type="text/plain",
            )
            return _failure_outcome(base_manifest, limitation)
        if upstream_limitation is not None:
            return _failure_outcome(base_manifest, upstream_limitation)
        limitation = _source_limitation(
            record,
            "source_unavailable",
            retrieved_at,
            reason="fixture payload is unavailable",
            http_status=503,
            retryable=True,
            release_blocking=False,
            official_upstream_evidence=False,
        )
        return _failure_outcome(base_manifest, limitation)
    content = zip_path.read_bytes()
    source = _source_metadata(record, content, retrieved_at)
    law = {
        "canonical_id": canonical_id,
        "display_code": source_path.upper(),
        "display_name": source_path,
        "source": source,
        "aliases": sorted({*record.get("alias_candidates", []), source_path, canonical_id}),
        "norm_count": 0,
        "stand_date": None,
    }
    try:
        parsed_norms = parse_gii_zip(zip_path, {"canonical_id": canonical_id}, source)
        parsed_norms = _normalize_generated_container_norms(parsed_norms)
        if not parsed_norms:
            raise ValueError("GII XML ZIP contained no parseable norms")
    except (ParseError, zipfile.BadZipFile, ValueError) as exc:
        limitation = _source_limitation(
            record,
            "parse_failed",
            retrieved_at,
            reason="GII XML ZIP parser failed",
            parser_version=GII_BULK_GENERATOR_VERSION,
            content_sha256=sha256_bytes(content),
            diagnostic=f"{exc.__class__.__name__}: {exc}",
            content_fetched=True,
        )
        return _failure_outcome(base_manifest, limitation)
    law["norm_count"] = len(parsed_norms)
    manifest_record = {
        **base_manifest,
        "terminal_state": "imported",
        "canonical_id": canonical_id,
        "source_url": record["xml_zip_url"],
        "content_sha256": sha256_bytes(content),
        "retrieved_at": retrieved_at,
        "parser_version": GII_BULK_GENERATOR_VERSION,
        "generated_law_ids": [canonical_id],
        "generated_norm_ids": [norm["canonical_id"] for norm in parsed_norms],
    }
    return {
        "terminal_state": "imported",
        "manifest_record": manifest_record,
        "law": law,
        "norms": parsed_norms,
        "limitation": None,
    }


def _failure_outcome(base_manifest: dict[str, Any], limitation: dict[str, Any]) -> dict[str, Any]:
    return {
        "terminal_state": limitation["terminal_state"],
        "manifest_record": {**base_manifest, **_manifest_failure_fields(limitation)},
        "law": None,
        "norms": [],
        "limitation": limitation,
    }


def _manifest_failure_fields(limitation: dict[str, Any]) -> dict[str, Any]:
    fields = dict(limitation)
    fields.pop("limitation_id", None)
    fields.pop("details", None)
    return fields


def _source_metadata(record: dict[str, Any], content: bytes, retrieved_at: str) -> dict[str, Any]:
    return {
        "source_kind": "gesetze-im-internet",
        "source_identifier": record["source_path"],
        "source_url": record["xml_zip_url"],
        "retrieved_at": retrieved_at,
        "stand_date": None,
        "stand_date_status": "not_exposed",
        "content_hash": sha256_bytes(content),
        "source_metadata": {
            "source_path": record["source_path"],
        },
        "known_issues": [],
    }


def _source_limitation(
    record: dict[str, Any],
    terminal_state: str,
    retrieved_at: str,
    *,
    reason: str,
    http_status: int | None = None,
    retryable: bool | None = None,
    release_blocking: bool = False,
    official_upstream_evidence: bool | None = None,
    content_sha256: str | None = None,
    content_type: str | None = None,
    parser_version: str | None = None,
    diagnostic: str | None = None,
    content_fetched: bool | None = None,
) -> dict[str, Any]:
    limitation = {
        **_base_manifest_source(record),
        "limitation_id": f"gii-{record['source_path']}-{terminal_state.replace('_', '-')}",
        "terminal_state": terminal_state,
        "source_url": record["xml_zip_url"],
        "retrieved_at": retrieved_at,
        "reason": reason,
        "details": {
            "source_path": record["source_path"],
            "release_blocking": release_blocking,
            "official_upstream_evidence": (
                official_upstream_evidence if official_upstream_evidence is not None else terminal_state == "source_unavailable"
            ),
        },
    }
    if http_status is not None:
        limitation["http_status"] = http_status
    if retryable is not None:
        limitation["retryable"] = retryable
    if content_sha256 is not None:
        limitation["content_sha256"] = content_sha256
    if content_type is not None:
        limitation["content_type"] = content_type
    if parser_version is not None:
        limitation["parser_version"] = parser_version
    if diagnostic is not None:
        limitation["diagnostic"] = diagnostic
    if content_fetched is not None:
        limitation["content_fetched"] = content_fetched
    return limitation


def _base_manifest_source(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_family": "gii",
        "source_id": f"gii:{record['source_path']}",
        "source_path": record["source_path"],
        "index_url": record["index_url"],
        "xml_zip_url": record["xml_zip_url"],
        "toc_url": record["toc_url"],
        "toc_sha256": record.get("toc_sha256") or "fixture-toc",
        "source_metadata": record.get("source_metadata", {}),
    }


def _build_manifest(
    discovery_artifact: dict[str, Any],
    discovered_sources: list[dict[str, Any]],
    source_limitations: list[dict[str, Any]],
    retrieved_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "gii-bulk-fixture",
        "package_id": f"gii-bulk-fixture-{retrieved_at}",
        "created_at": retrieved_at,
        "validation_mode": "terminal",
        "generator": {"name": "gii-bulk-fixture", "version": GII_BULK_GENERATOR_VERSION},
        "parser_versions": {"gii_xml": GII_BULK_GENERATOR_VERSION},
        "discovered_sources": discovered_sources,
        "canonical_ids": [
            {"canonical_id": record["canonical_id"], "source_family": "gii", "source_id": record["source_id"]}
            for record in discovered_sources
            if record.get("terminal_state") == "imported"
        ],
        "relationship_sources": [],
        "source_limitations": source_limitations,
        "generated_package": {
            "schema_version": "generated-package.v1",
            "generated_at": retrieved_at,
            "record_counts": {
                "discovered_sources": discovery_artifact.get("discovered_gii_items", len(discovered_sources)),
                "source_limitations": len(source_limitations),
            },
            "manifest_hash": "computed-in-package",
            "package_files": ["laws.json", "norms.json", "manifest.json", "source-limitations.json"],
        },
    }


def _write_generated_package(
    *,
    package_dir: Path,
    laws: list[dict[str, Any]],
    norms: list[dict[str, Any]],
    manifest: dict[str, Any],
    source_limitations: list[dict[str, Any]],
    retrieved_at: str,
    discovered_count: int,
    imported_count: int,
) -> None:
    files: dict[str, Any] = {
        "laws.json": laws,
        "norms.json": norms,
        "manifest.json": manifest,
        "source-limitations.json": source_limitations,
        "relationships.json": [],
        "readiness.json": {
            "stage": "normalized_dataset",
            "state": "ready",
            "details": {"law_count": len(laws), "norm_count": len(norms)},
        },
        "search-index.json": {"documents": []},
    }
    for name, data in files.items():
        (package_dir / name).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    package = {
        "schema_version": "generated-package.v1",
        "dataset_id": "gii-bulk-fixture",
        "package_id": f"gii-bulk-fixture-{retrieved_at}",
        "generated_at": retrieved_at,
        "generator": {"name": "gii-bulk-fixture", "version": GII_BULK_GENERATOR_VERSION},
        "manifest_path": "manifest.json",
        "readiness_path": "readiness.json",
        "record_counts": {
            "laws": len(laws),
            "norms": len(norms),
            "relationships": 0,
            "source_limitations": len(source_limitations),
            "discovered_sources": discovered_count,
            "imported_sources": imported_count,
        },
        "content_hashes": {
            name: f"sha256:{_file_sha256(package_dir / name)}"
            for name in files
        },
        "validation_mode": "terminal",
        "source_families": ["gii"],
    }
    (package_dir / "package.json").write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _discovered_records(discovery_artifact: dict[str, Any]) -> list[dict[str, Any]]:
    records = discovery_artifact.get("discovered_gii_records")
    if records is None:
        records = discovery_artifact.get("discovered_sources")
    if not isinstance(records, list):
        raise ValueError("discovery artifact must contain discovered_gii_records")
    return records


def _normalize_generated_container_norms(norms: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for norm in norms:
        item = dict(norm)
        if item.get("status") == "container" and not item.get("text"):
            item["unit"] = "container"
            item.pop("text", None)
        normalized.append(item)
    return normalized


def _upstream_limitations_by_source_path(limitations: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    indexed: dict[str, dict[str, Any]] = {}
    for limitation in limitations:
        source_path = limitation.get("source_path")
        if isinstance(source_path, str):
            indexed[source_path] = limitation
    return indexed


def _parser_variant_matrix(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {
            "version": "fixture-v1",
            "covered_variants": [],
        }
    matrix = json.loads(path.read_text(encoding="utf-8"))
    return {
        "version": matrix["version"],
        "path": str(path),
        "sha256": _file_sha256(path),
        "covered_variants": matrix.get("covered_variants", []),
    }


def _canonical_id_for_source_path(source_path: str) -> str:
    for spec in SOURCE_SPECS.values():
        if spec.source_kind != "gesetze-im-internet":
            continue
        if (spec.metadata or {}).get("source_path") == source_path:
            return spec.canonical_id
    return source_path


def _is_release_blocking_upstream_limitation(limitation: dict[str, Any] | None) -> bool:
    if not limitation:
        return False
    details = limitation.get("details") if isinstance(limitation.get("details"), dict) else {}
    return (
        limitation.get("terminal_state") == "source_unavailable"
        and details.get("release_blocking") is True
        and details.get("official_upstream_evidence") is True
    )


def _hash_package(package_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(package_dir.glob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
