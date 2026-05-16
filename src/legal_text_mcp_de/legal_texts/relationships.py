# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

from .manifest import SOURCE_FAMILIES
from .validation import RELATIONSHIP_ENDPOINT_KINDS, RELATIONSHIP_TYPES


DATA_DIR = Path(__file__).parent / "data"
DEFAULT_SCOPE_POLICY_PATH = DATA_DIR / "dsgvo_scope_policy.v1.json"
DEFAULT_PRIVACY_SCOPE_SEED_PATH = DATA_DIR / "privacy_scope_seed.v1.json"

SCOPE_POLICY_SCHEMA_VERSION = "dsgvo-scope-policy.v1"
PRIVACY_SCOPE_SEED_SCHEMA_VERSION = "privacy-scope-seed.v1"
ALLOWED_POLICY_USES = {"manual_seed_only", "automated_metadata_allowed", "excluded"}
ALLOWED_SOURCE_BASES = {"manual_seed", "approved_metadata", "policy_excluded"}
MINIMUM_EU_NEIGHBOR_CELEXS = {"32024R1689", "32023R2854"}
COPIED_TEXT_FIELDS = {
    "copied_text",
    "editorial_text",
    "copied_editorial_text",
    "third_party_text",
    "html_text",
    "text",
}
REQUIRED_SCOPE_POLICY_FIELDS = {
    "schema_version",
    "policy_id",
    "source_url",
    "reviewed_at",
    "robots_reviewed_at",
    "robots_result",
    "terms_reviewed_at",
    "terms_result",
    "allowed_use",
    "no_editorial_text_copied",
}
REQUIRED_SEED_FIELDS = {
    "schema_version",
    "policy_id",
    "maintained_at",
    "source_basis",
    "relationship_source",
    "official_targets",
    "source_limitations",
    "relationships",
}
REQUIRED_RELATIONSHIP_FIELDS = {
    "relationship_id",
    "relationship_type",
    "subject",
    "object",
    "source_basis",
    "provenance",
}
REQUIRED_LIMITATION_FIELDS = {
    "limitation_id",
    "source_family",
    "source_id",
    "terminal_state",
    "source_url",
    "reason",
    "details",
}


def load_scope_policy(path: Path = DEFAULT_SCOPE_POLICY_PATH) -> dict[str, Any]:
    return _load_json_object(path)


def load_privacy_scope_seed(path: Path = DEFAULT_PRIVACY_SCOPE_SEED_PATH) -> dict[str, Any]:
    return _load_json_object(path)


def validate_scope_policy(policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(policy, dict):
        return ["scope policy must be an object"]
    missing = REQUIRED_SCOPE_POLICY_FIELDS - set(policy)
    if missing:
        errors.append(f"scope policy missing fields {sorted(missing)}")
    if policy.get("schema_version") != SCOPE_POLICY_SCHEMA_VERSION:
        errors.append(f"scope policy schema_version must be {SCOPE_POLICY_SCHEMA_VERSION}")
    if policy.get("allowed_use") not in ALLOWED_POLICY_USES:
        errors.append(f"scope policy allowed_use must be one of {sorted(ALLOWED_POLICY_USES)}")
    if policy.get("no_editorial_text_copied") is not True:
        errors.append("scope policy requires no_editorial_text_copied=true")
    if policy.get("allowed_use") in {"manual_seed_only", "excluded"} and not policy.get("fallback_seed_path"):
        errors.append(f"{policy.get('allowed_use')} policy requires fallback_seed_path")
    if not _https(policy.get("source_url")):
        errors.append("scope policy source_url must be HTTPS")
    forbidden = _find_forbidden_field_paths(policy)
    if forbidden:
        errors.append(f"scope policy must not include copied/editorial text fields {forbidden}")
    return errors


def validate_privacy_scope_seed(seed: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(seed, dict):
        return ["seed graph must be an object"]
    missing = REQUIRED_SEED_FIELDS - set(seed)
    if missing:
        errors.append(f"seed graph missing fields {sorted(missing)}")
    if seed.get("schema_version") != PRIVACY_SCOPE_SEED_SCHEMA_VERSION:
        errors.append(f"seed graph schema_version must be {PRIVACY_SCOPE_SEED_SCHEMA_VERSION}")
    if seed.get("policy_id") != policy.get("policy_id"):
        errors.append(f"seed policy_id {seed.get('policy_id')} does not match scope policy {policy.get('policy_id')}")
    source_basis = seed.get("source_basis")
    if source_basis not in ALLOWED_SOURCE_BASES:
        errors.append(f"seed source_basis must be one of {sorted(ALLOWED_SOURCE_BASES)}")
    if source_basis == "approved_metadata" and policy.get("allowed_use") != "automated_metadata_allowed":
        errors.append("approved_metadata seeds require automated_metadata_allowed policy")
    if policy.get("allowed_use") in {"manual_seed_only", "excluded"} and not policy.get("fallback_seed_path"):
        errors.append(f"{policy.get('allowed_use')} policy requires fallback_seed_path")
    forbidden = _find_forbidden_field_paths(seed)
    if forbidden:
        errors.append(f"seed graph must not include copied/editorial text fields {forbidden}")

    relationship_source = seed.get("relationship_source")
    if isinstance(relationship_source, dict):
        errors.extend(_validate_relationship_source(relationship_source, policy))
    elif "relationship_source" in seed:
        errors.append("relationship_source must be an object")

    target_ids = _target_ids(seed.get("official_targets"))
    errors.extend(_validate_official_targets(seed.get("official_targets")))
    limitation_ids, celex_values = _validate_seed_limitations(seed.get("source_limitations"), errors)
    celex_values.update(_official_target_celex_values(seed.get("official_targets")))
    for celex in sorted(MINIMUM_EU_NEIGHBOR_CELEXS - celex_values):
        errors.append(f"minimum EU neighbor CELEX {celex} is missing")
    errors.extend(_validate_seed_relationships(seed.get("relationships"), target_ids, limitation_ids))
    return errors


def seed_relationship_source_to_manifest_record(seed: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(seed["relationship_source"])


def seed_limitations_to_package_records(seed: dict[str, Any]) -> list[dict[str, Any]]:
    return deepcopy(seed.get("source_limitations", []))


def seed_relationships_to_package_records(
    seed: dict[str, Any],
    *,
    resolved_limitations: dict[str, dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    relationship_source = seed["relationship_source"]
    resolved_limitations = resolved_limitations or {}
    records: list[dict[str, Any]] = []
    for relationship in seed.get("relationships", []):
        metadata = deepcopy(relationship.get("metadata", {}))
        metadata["source_basis"] = relationship.get("source_basis")
        object_endpoint = deepcopy(relationship["object"])
        if object_endpoint.get("kind") == "source_limitation" and object_endpoint.get("id") in resolved_limitations:
            object_endpoint = deepcopy(resolved_limitations[object_endpoint["id"]])
        records.append(
            {
                "relationship_id": relationship["relationship_id"],
                "relationship_type": relationship["relationship_type"],
                "subject": deepcopy(relationship["subject"]),
                "object": object_endpoint,
                "source_family": relationship_source["source_family"],
                "source_id": relationship_source["source_id"],
                "provenance": deepcopy(relationship["provenance"]),
                "metadata": metadata,
            }
        )
    return records


def _load_json_object(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return data


def _validate_relationship_source(source: dict[str, Any], policy: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    missing = {
        "relationship_source_id",
        "source_family",
        "source_id",
        "provider",
        "source_url",
        "robots_reviewed_at",
        "terms_reviewed_at",
        "policy_review_reference",
        "allowed_use",
        "target_official_record",
        "no_editorial_text_copied",
    } - set(source)
    if missing:
        errors.append(f"relationship_source missing fields {sorted(missing)}")
    if source.get("source_family") != "third-party-scope":
        errors.append("relationship_source source_family must be third-party-scope")
    if source.get("source_id") and not str(source["source_id"]).startswith("third-party-scope:"):
        errors.append("relationship_source source_id must start with third-party-scope:")
    if source.get("allowed_use") != policy.get("allowed_use"):
        errors.append("relationship_source allowed_use must match scope policy")
    if source.get("no_editorial_text_copied") is not True:
        errors.append("relationship_source requires no_editorial_text_copied=true")
    if not _https(source.get("source_url")):
        errors.append("relationship_source source_url must be HTTPS")
    return errors


def _validate_official_targets(targets: Any) -> list[str]:
    if not isinstance(targets, dict):
        return ["official_targets must be an object"]
    errors: list[str] = []
    for key, expected_kind in (("laws", "law"), ("norms", "norm")):
        values = targets.get(key)
        if not isinstance(values, list):
            errors.append(f"official_targets.{key} must be a list")
            continue
        seen: set[str] = set()
        for index, target in enumerate(values):
            owner = f"official_targets.{key}[{index}]"
            if not isinstance(target, dict):
                errors.append(f"{owner} must be an object")
                continue
            if target.get("kind") != expected_kind:
                errors.append(f"{owner} kind must be {expected_kind}")
            target_id = target.get("id")
            if not isinstance(target_id, str) or not target_id.strip():
                errors.append(f"{owner} id must be a non-empty string")
            elif target_id in seen:
                errors.append(f"duplicate official target {expected_kind}:{target_id}")
            seen.add(target_id)
            source_family = target.get("source_family")
            if source_family not in SOURCE_FAMILIES:
                errors.append(f"{owner} unsupported source_family {source_family}")
            celex = target.get("celex")
            if source_family == "eur-lex-cellar" and celex is not None and not _valid_celex(celex):
                errors.append(f"{owner} invalid CELEX {celex}")
    return errors


def _validate_seed_limitations(limitations: Any, errors: list[str]) -> tuple[set[str], set[str]]:
    limitation_ids: set[str] = set()
    celex_values: set[str] = set()
    if not isinstance(limitations, list):
        errors.append("source_limitations must be a list")
        return limitation_ids, celex_values
    for index, limitation in enumerate(limitations):
        owner = (
            str(limitation.get("limitation_id") or f"source_limitations[{index}]")
            if isinstance(limitation, dict)
            else f"source_limitations[{index}]"
        )
        if not isinstance(limitation, dict):
            errors.append(f"{owner} must be an object")
            continue
        missing = REQUIRED_LIMITATION_FIELDS - set(limitation)
        if missing:
            errors.append(f"{owner}: source limitation missing fields {sorted(missing)}")
        limitation_id = limitation.get("limitation_id")
        if isinstance(limitation_id, str):
            if limitation_id in limitation_ids:
                errors.append(f"duplicate limitation_id {limitation_id}")
            limitation_ids.add(limitation_id)
        if limitation.get("source_family") not in SOURCE_FAMILIES:
            errors.append(f"{owner}: unsupported source_family {limitation.get('source_family')}")
        if limitation.get("terminal_state") == "imported":
            errors.append(f"{owner}: source limitation terminal_state must not be imported")
        if "retrieved_at" not in limitation and "decided_at" not in limitation:
            errors.append(f"{owner}: source limitation requires retrieved_at or decided_at")
        if limitation.get("source_family") == "eur-lex-cellar":
            celex = limitation.get("celex")
            if not _valid_celex(celex):
                errors.append(f"{owner}: invalid CELEX {celex}")
            else:
                celex_values.add(str(celex))
        if limitation.get("source_family") == "state-law" and not _https(limitation.get("official_source_url")):
            errors.append(f"{owner}: state-law limitation requires official_source_url")
    return limitation_ids, celex_values


def _validate_seed_relationships(
    relationships: Any,
    target_ids: dict[str, set[str]],
    limitation_ids: set[str],
) -> list[str]:
    if not isinstance(relationships, list):
        return ["relationships must be a list"]
    errors: list[str] = []
    seen: set[str] = set()
    for index, relationship in enumerate(relationships):
        owner = (
            str(relationship.get("relationship_id") or f"relationships[{index}]")
            if isinstance(relationship, dict)
            else f"relationships[{index}]"
        )
        if not isinstance(relationship, dict):
            errors.append(f"{owner} must be an object")
            continue
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
        if relationship.get("source_basis") not in ALLOWED_SOURCE_BASES:
            errors.append(f"{owner}: source_basis must be one of {sorted(ALLOWED_SOURCE_BASES)}")
        provenance = relationship.get("provenance")
        if isinstance(provenance, dict):
            provenance_missing = {"basis", "source_url"} - set(provenance)
            if provenance_missing:
                errors.append(f"{owner}: provenance missing fields {sorted(provenance_missing)}")
        elif "provenance" in relationship:
            errors.append(f"{owner}: provenance must be an object")
        for endpoint_name in ("subject", "object"):
            errors.extend(
                _validate_seed_endpoint(
                    owner, endpoint_name, relationship.get(endpoint_name), target_ids, limitation_ids
                )
            )
    return errors


def _validate_seed_endpoint(
    owner: str,
    endpoint_name: str,
    endpoint: Any,
    target_ids: dict[str, set[str]],
    limitation_ids: set[str],
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
    if kind == "source_limitation":
        if target_id not in limitation_ids:
            return [
                f"{owner}: {endpoint_name} target source_limitation:{target_id} is not declared as a source limitation"
            ]
        return []
    if target_id not in target_ids.get(kind, set()):
        return [f"{owner}: {endpoint_name} target {kind}:{target_id} is not declared as an official target"]
    return []


def _target_ids(targets: Any) -> dict[str, set[str]]:
    result = {"law": set(), "norm": set()}
    if not isinstance(targets, dict):
        return result
    for key, kind in (("laws", "law"), ("norms", "norm")):
        values = targets.get(key)
        if not isinstance(values, list):
            continue
        for target in values:
            if isinstance(target, dict) and isinstance(target.get("id"), str):
                result[kind].add(target["id"])
    return result


def _official_target_celex_values(targets: Any) -> set[str]:
    values: set[str] = set()
    if not isinstance(targets, dict):
        return values
    for records in targets.values():
        if not isinstance(records, list):
            continue
        for record in records:
            if isinstance(record, dict) and _valid_celex(record.get("celex")):
                values.add(record["celex"])
    return values


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


def _https(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://")


def _valid_celex(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"3\d{4}[A-Z]\d{4}", value) is not None
