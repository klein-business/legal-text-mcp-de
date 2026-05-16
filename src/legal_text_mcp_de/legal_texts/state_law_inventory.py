# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from .manifest import validate_corpus_manifest


DATA_DIR = Path(__file__).parent / "data"
DEFAULT_STATE_LAW_INVENTORY_PATH = DATA_DIR / "state_law_sources.v1.json"
DEFAULT_STATE_LAW_LIMITATIONS_PATH = DATA_DIR / "state_law_limitations.v1.json"

STATE_LAW_INVENTORY_SCHEMA_VERSION = "state-law-sources.v1"
STATE_LAW_LIMITATIONS_SCHEMA_VERSION = "state-law-limitations.v1"
FIXED_STATES: dict[str, str] = {
    "BW": "Baden-Wuerttemberg",
    "BY": "Bayern",
    "BE": "Berlin",
    "BB": "Brandenburg",
    "HB": "Bremen",
    "HH": "Hamburg",
    "HE": "Hessen",
    "MV": "Mecklenburg-Vorpommern",
    "NI": "Niedersachsen",
    "NW": "Nordrhein-Westfalen",
    "RP": "Rheinland-Pfalz",
    "SL": "Saarland",
    "SN": "Sachsen",
    "ST": "Sachsen-Anhalt",
    "SH": "Schleswig-Holstein",
    "TH": "Thueringen",
}
FIXED_STATE_CODES: tuple[str, ...] = tuple(FIXED_STATES)
ADAPTER_CLASSES = {"machine_readable", "stable_html", "pdf", "limitation_only"}
SOURCE_FORMATS = {"xml", "json", "html", "pdf", "unknown"}
REQUIRED_INVENTORY_FIELDS = {
    "state_code",
    "state_name",
    "law_slug",
    "law_id",
    "official_sources",
    "source_format",
    "adapter_class",
    "reachability",
    "stability_note",
}


def derive_state_law_id(state_code: str, law_slug: str) -> str:
    normalized_code = state_code.lower()
    if normalized_code.upper() not in FIXED_STATES:
        raise ValueError(f"unknown state_code {state_code}")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", law_slug):
        raise ValueError(f"invalid law_slug {law_slug}")
    return f"state:{normalized_code}/{law_slug}"


def load_state_law_inventory(path: Path = DEFAULT_STATE_LAW_INVENTORY_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("state-law inventory must be an object")
    return data


def load_state_law_limitations(path: Path = DEFAULT_STATE_LAW_LIMITATIONS_PATH) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("state-law limitations must be an object")
    if data.get("schema_version") != STATE_LAW_LIMITATIONS_SCHEMA_VERSION:
        raise ValueError(f"state-law limitations schema_version must be {STATE_LAW_LIMITATIONS_SCHEMA_VERSION}")
    limitations = data.get("limitations")
    if not isinstance(limitations, list) or not all(isinstance(item, dict) for item in limitations):
        raise ValueError("state-law limitations must contain a limitations list of objects")
    return limitations


def validate_state_law_inventory(inventory: dict[str, Any], limitations: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    if not isinstance(inventory, dict):
        return ["state-law inventory must be an object"]
    if inventory.get("schema_version") != STATE_LAW_INVENTORY_SCHEMA_VERSION:
        errors.append(f"state-law inventory schema_version must be {STATE_LAW_INVENTORY_SCHEMA_VERSION}")
    states = inventory.get("states")
    if not isinstance(states, list):
        return errors + ["states must be a list"]
    limitation_ids = {
        limitation.get("limitation_id")
        for limitation in limitations
        if isinstance(limitation, dict) and isinstance(limitation.get("limitation_id"), str)
    }

    seen: set[str] = set()
    for index, record in enumerate(states):
        if not isinstance(record, dict):
            errors.append(f"states[{index}] must be an object")
            continue
        owner = str(record.get("state_code") or f"states[{index}]")
        state_code = record.get("state_code")
        if state_code in seen:
            errors.append(f"duplicate state inventory record {state_code}")
        if isinstance(state_code, str):
            seen.add(state_code)
        errors.extend(_validate_inventory_record(owner, record, limitation_ids))

    missing = sorted(set(FIXED_STATE_CODES) - seen)
    unknown = sorted(seen - set(FIXED_STATE_CODES))
    if missing:
        errors.append(f"missing state inventory records {missing}")
    for state_code in unknown:
        errors.append(f"unknown state_code {state_code}")
    errors.extend(_validate_limitations(limitations))
    return errors


def inventory_records_to_manifest_sources(
    inventory: dict[str, Any],
    limitations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    # Phase 8 is inventory-only. Manifest terminal evidence is represented by
    # source limitations until parser phases create imported state-law records.
    return deepcopy(limitations)


def _validate_inventory_record(owner: str, record: dict[str, Any], limitation_ids: set[Any]) -> list[str]:
    errors: list[str] = []
    missing = REQUIRED_INVENTORY_FIELDS - set(record)
    if missing:
        errors.append(f"{owner}: inventory record missing fields {sorted(missing)}")
    state_code = record.get("state_code")
    if state_code in FIXED_STATES and record.get("state_name") != FIXED_STATES[state_code]:
        errors.append(f"{owner}: state_name {record.get('state_name')} does not match {FIXED_STATES[state_code]}")
    law_slug = record.get("law_slug")
    law_id = record.get("law_id")
    if isinstance(state_code, str) and isinstance(law_slug, str):
        try:
            expected_law_id = derive_state_law_id(state_code, law_slug)
        except ValueError as exc:
            errors.append(f"{owner}: {exc}")
        else:
            if law_id != expected_law_id:
                errors.append(f"{owner}: law_id {law_id} does not match expected {expected_law_id}")
    source_format = record.get("source_format")
    if source_format not in SOURCE_FORMATS:
        errors.append(f"{owner}: unsupported source_format {source_format}")
    adapter_class = record.get("adapter_class")
    if adapter_class not in ADAPTER_CLASSES:
        errors.append(f"{owner}: unsupported adapter_class {adapter_class}")
    official_sources = record.get("official_sources")
    if not isinstance(official_sources, list) or not official_sources:
        errors.append(f"{owner}: official_sources must contain at least one source")
    elif all(isinstance(source, dict) for source in official_sources):
        for source_index, source in enumerate(official_sources):
            source_owner = f"{owner}.official_sources[{source_index}]"
            for field in ("url", "format", "publisher"):
                if field not in source:
                    errors.append(f"{source_owner}: missing {field}")
            if not _https(source.get("url")):
                errors.append(f"{source_owner}: url must be HTTPS")
            if source.get("format") not in SOURCE_FORMATS:
                errors.append(f"{source_owner}: unsupported format {source.get('format')}")
    else:
        errors.append(f"{owner}: official_sources must be a list of objects")
    reachability = record.get("reachability")
    if not isinstance(reachability, dict):
        errors.append(f"{owner}: reachability must be an object")
    else:
        for field in ("checked_at", "status", "content_type"):
            if field not in reachability:
                errors.append(f"{owner}: reachability missing {field}")
    if not isinstance(record.get("stability_note"), str) or not record.get("stability_note", "").strip():
        errors.append(f"{owner}: stability_note must be a non-empty string")
    if adapter_class == "limitation_only":
        limitation_id = record.get("source_limitation_id")
        if not limitation_id:
            errors.append(f"{owner}: limitation_only requires source_limitation_id")
        elif limitation_id not in limitation_ids:
            errors.append(f"{owner}: source_limitation_id {limitation_id} not found")
    return errors


def _validate_limitations(limitations: list[dict[str, Any]]) -> list[str]:
    if not isinstance(limitations, list):
        return ["limitations must be a list"]
    manifest = {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "state-law-limitations",
        "package_id": "state-law-limitations",
        "created_at": "2026-05-15T00:00:00Z",
        "validation_mode": "terminal",
        "generator": {"name": "state-law-inventory", "version": "1"},
        "parser_versions": {"state_law_inventory": "1"},
        "discovered_sources": [],
        "canonical_ids": [],
        "relationship_sources": [],
        "source_limitations": limitations,
    }
    return [f"state-law limitations: {error}" for error in validate_corpus_manifest(manifest, require_terminal_states=True)]


def _https(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://")
