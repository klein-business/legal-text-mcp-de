# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .state_law_inventory import FIXED_STATE_CODES
from .validation import validate_generated_package


STATE_LAW_COVERAGE_SCHEMA_VERSION = "state-law-coverage.v1"
STATE_LAW_PDF_GATE_SCHEMA_VERSION = "state-law-pdf-source-gate.v1"


def build_state_law_coverage(
    inventory: dict[str, Any],
    phase9_artifact: dict[str, Any],
    *,
    package_dir: Path,
) -> dict[str, Any]:
    outcomes = (
        phase9_artifact.get("source_outcomes") if isinstance(phase9_artifact.get("source_outcomes"), dict) else {}
    )
    states: list[dict[str, Any]] = []
    for record in inventory.get("states", []):
        if not isinstance(record, dict):
            continue
        law_id = record.get("law_id")
        outcome = outcomes.get(law_id)
        entry = _base_entry(record, package_dir)
        if isinstance(outcome, dict):
            terminal_state = outcome.get("terminal_state")
            entry["terminal_state"] = terminal_state
            entry["source_url"] = _outcome_source_url(outcome, record)
            if terminal_state == "imported":
                entry["law_id"] = law_id
                entry["evidence"] = {
                    **entry["evidence"],
                    "phase9_terminal_state": "imported",
                    "generated_package_file": "laws.json",
                }
            else:
                limitation_id = _outcome_limitation_id(outcome)
                if limitation_id:
                    entry["source_limitation_id"] = limitation_id
                entry["evidence"] = {
                    **entry["evidence"],
                    "phase9_terminal_state": terminal_state,
                    "generated_package_file": "source-limitations.json",
                }
        else:
            entry["terminal_state"] = "missing"
            entry["evidence"] = {**entry["evidence"], "phase9_terminal_state": "missing"}
        states.append(entry)
    counts = _coverage_counts(inventory, states)
    return {
        "schema_version": STATE_LAW_COVERAGE_SCHEMA_VERSION,
        "phase": "phase-10",
        "coverage_basis": "phase9-imported-or-limited",
        "package_dir": str(package_dir),
        "counts": counts,
        "states": sorted(states, key=lambda item: item["state_code"]),
    }


def validate_state_law_coverage(
    coverage: dict[str, Any],
    inventory: dict[str, Any],
    phase9_artifact: dict[str, Any],
    *,
    package_dir: Path,
) -> list[str]:
    errors: list[str] = []
    if coverage.get("schema_version") != STATE_LAW_COVERAGE_SCHEMA_VERSION:
        errors.append(f"schema_version must be {STATE_LAW_COVERAGE_SCHEMA_VERSION}")
    states = coverage.get("states")
    if not isinstance(states, list):
        return errors + ["states must be a list"]
    inventory_records = {
        record.get("state_code"): record for record in inventory.get("states", []) if isinstance(record, dict)
    }
    law_ids = {law.get("canonical_id") for law in _load_json_list(package_dir / "laws.json")}
    limitations_by_id = {
        item.get("limitation_id"): item
        for item in _load_json_list(package_dir / "source-limitations.json")
        if isinstance(item.get("limitation_id"), str)
    }
    limitation_ids = set(limitations_by_id)
    seen: set[str] = set()
    for entry in states:
        if not isinstance(entry, dict):
            errors.append("coverage states entries must be objects")
            continue
        state_code = entry.get("state_code")
        if isinstance(state_code, str):
            if state_code in seen:
                errors.append(f"duplicate coverage state {state_code}")
            seen.add(state_code)
        record = inventory_records.get(state_code)
        if record is None:
            errors.append(f"coverage state {state_code} is not in inventory")
            continue
        if entry.get("adapter_class") != record.get("adapter_class"):
            errors.append(
                f"{state_code}: adapter_class {entry.get('adapter_class')} does not match inventory {record.get('adapter_class')}"
            )
        if entry.get("source_format") != record.get("source_format"):
            errors.append(
                f"{state_code}: source_format {entry.get('source_format')} does not match inventory {record.get('source_format')}"
            )
        terminal_state = entry.get("terminal_state")
        if terminal_state == "imported":
            law_id = entry.get("law_id")
            if law_id not in law_ids:
                errors.append(f"{state_code}: law_id {law_id} not found in package laws.json")
        elif terminal_state in {"parse_failed", "source_unavailable", "unsupported_format", "excluded_by_policy"}:
            limitation_id = entry.get("source_limitation_id")
            if limitation_id not in limitation_ids:
                errors.append(
                    f"{state_code}: source_limitation_id {limitation_id} not found in package source-limitations.json"
                )
            else:
                errors.extend(_validate_limitation_binding(entry, limitations_by_id[limitation_id]))
        elif terminal_state == "missing":
            errors.append(f"{state_code}: missing phase9 outcome for {record.get('law_id')}")
        else:
            errors.append(f"{state_code}: missing terminal coverage")
    missing = sorted(set(FIXED_STATE_CODES) - seen)
    unknown = sorted(seen - set(FIXED_STATE_CODES))
    if missing:
        errors.append(f"missing coverage states {missing}")
    if unknown:
        errors.append(f"unknown coverage states {unknown}")
    if len(states) != len(FIXED_STATE_CODES):
        errors.append(f"coverage must contain exactly {len(FIXED_STATE_CODES)} states")
    expected_counts = _coverage_counts(inventory, [entry for entry in states if isinstance(entry, dict)])
    if coverage.get("counts") != expected_counts:
        errors.append(f"coverage counts {coverage.get('counts')} do not match expected {expected_counts}")
    phase9_errors = phase9_artifact.get("validation_errors")
    if isinstance(phase9_errors, list) and phase9_errors:
        errors.extend(f"phase9: {error}" for error in phase9_errors)
    errors.extend(f"package: {error}" for error in validate_generated_package(package_dir, require_search_index=True))
    return errors


def _validate_limitation_binding(entry: dict[str, Any], limitation: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    state_code = entry.get("state_code")
    limitation_id = entry.get("source_limitation_id")
    if limitation.get("source_id") != entry.get("source_id"):
        errors.append(
            f"{state_code}: source_limitation_id {limitation_id} source_id {limitation.get('source_id')} "
            f"does not match coverage source_id {entry.get('source_id')}"
        )
    limitation_state_code = limitation.get("state_code")
    if isinstance(limitation_state_code, str) and isinstance(state_code, str):
        if limitation_state_code.casefold() != state_code.casefold():
            errors.append(
                f"{state_code}: source_limitation_id {limitation_id} state_code {limitation_state_code} "
                f"does not match coverage state_code {state_code}"
            )
    elif limitation_state_code != state_code:
        errors.append(
            f"{state_code}: source_limitation_id {limitation_id} state_code {limitation_state_code} "
            f"does not match coverage state_code {state_code}"
        )
    if limitation.get("terminal_state") != entry.get("terminal_state"):
        errors.append(
            f"{state_code}: source_limitation_id {limitation_id} terminal_state {limitation.get('terminal_state')} "
            f"does not match coverage terminal_state {entry.get('terminal_state')}"
        )
    return errors


def build_state_law_pdf_gate_artifact(
    inventory: dict[str, Any],
    phase9_artifact: dict[str, Any],
    *,
    package_dir: Path,
    coverage_path: Path,
) -> dict[str, Any]:
    coverage = build_state_law_coverage(inventory, phase9_artifact, package_dir=package_dir)
    coverage_path.parent.mkdir(parents=True, exist_ok=True)
    coverage_path.write_text(
        json.dumps(coverage, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    errors = validate_state_law_coverage(coverage, inventory, phase9_artifact, package_dir=package_dir)
    return {
        "schema_version": STATE_LAW_PDF_GATE_SCHEMA_VERSION,
        "phase": "phase-10",
        "coverage_path": str(coverage_path),
        "coverage_sha256": _file_sha256(coverage_path),
        "package_dir": str(package_dir),
        "package_sha256": _hash_package(package_dir),
        "counts": coverage["counts"],
        "pdf_status": "no_pdf_adapter_class_records_in_current_inventory",
        "validation_errors": errors,
    }


def _base_entry(record: dict[str, Any], package_dir: Path) -> dict[str, Any]:
    source = record.get("official_sources", [{}])[0] if isinstance(record.get("official_sources"), list) else {}
    state_code = str(record.get("state_code"))
    law_slug = str(record.get("law_slug"))
    return {
        "state_code": state_code,
        "state_name": record.get("state_name"),
        "adapter_class": record.get("adapter_class"),
        "source_format": record.get("source_format"),
        "source_id": f"state-law:{state_code.lower()}/{law_slug}",
        "source_url": source.get("url"),
        "evidence": {
            "package_dir": str(package_dir),
            "phase9_artifact": "adapter-gate.json",
            "phase8_inventory": "state_law_sources.v1.json",
        },
    }


def _coverage_counts(inventory: dict[str, Any], states: list[dict[str, Any]]) -> dict[str, int]:
    imported = sum(1 for entry in states if entry.get("terminal_state") == "imported")
    limited = sum(
        1
        for entry in states
        if entry.get("terminal_state")
        in {"parse_failed", "source_unavailable", "unsupported_format", "excluded_by_policy"}
    )
    pdf_sources = sum(
        1 for record in inventory.get("states", []) if isinstance(record, dict) and record.get("adapter_class") == "pdf"
    )
    return {
        "total_states": len(states),
        "imported": imported,
        "limited": limited,
        "pdf_source_count": pdf_sources,
        "pdf_extraction_count": 0,
    }


def _outcome_limitation_id(outcome: dict[str, Any]) -> str | None:
    limitation = outcome.get("limitation")
    if isinstance(limitation, dict) and isinstance(limitation.get("limitation_id"), str):
        return limitation["limitation_id"]
    value = outcome.get("limitation_id") or outcome.get("source_limitation_id")
    return value if isinstance(value, str) else None


def _outcome_source_url(outcome: dict[str, Any], record: dict[str, Any]) -> str | None:
    manifest = outcome.get("manifest_record")
    if isinstance(manifest, dict) and isinstance(manifest.get("source_url"), str):
        return manifest["source_url"]
    limitation = outcome.get("limitation")
    if isinstance(limitation, dict) and isinstance(limitation.get("source_url"), str):
        return limitation["source_url"]
    source = record.get("official_sources", [{}])[0] if isinstance(record.get("official_sources"), list) else {}
    value = source.get("url") if isinstance(source, dict) else None
    return value if isinstance(value, str) else None


def _load_json_list(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        return []
    return [item for item in data if isinstance(item, dict)]


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _hash_package(package_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(package_dir.glob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()
