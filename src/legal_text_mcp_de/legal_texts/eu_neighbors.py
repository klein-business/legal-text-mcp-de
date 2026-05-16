# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

from .eurlex_xml import parse_eurlex_act_xml
from .relationships import MINIMUM_EU_NEIGHBOR_CELEXS
from .sources import SourceSpec


DATA_DIR = Path(__file__).parent / "data"
DEFAULT_EU_NEIGHBOR_SOURCES_PATH = DATA_DIR / "eu_neighbor_sources.v1.json"
EU_NEIGHBOR_SOURCES_SCHEMA_VERSION = "eu-neighbor-sources.v1"


def load_eu_neighbor_source_records(path: Path = DEFAULT_EU_NEIGHBOR_SOURCES_PATH) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("EU neighbor source file must contain an object")
    if data.get("schema_version") != EU_NEIGHBOR_SOURCES_SCHEMA_VERSION:
        raise ValueError(f"EU neighbor source file schema_version must be {EU_NEIGHBOR_SOURCES_SCHEMA_VERSION}")
    sources = data.get("sources")
    if not isinstance(sources, list) or not all(isinstance(source, dict) for source in sources):
        raise ValueError("EU neighbor sources must be a list of objects")
    return sources


def validate_eu_neighbor_source_records(records: list[dict[str, Any]], seed: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seed_celexes = _seed_eu_celexes(seed)
    for celex in sorted(MINIMUM_EU_NEIGHBOR_CELEXS - seed_celexes):
        errors.append(f"required EU neighbor CELEX {celex} is missing from privacy scope seed")

    seen_canonical_ids: set[str] = set()
    seen_celexes: set[str] = set()
    for index, record in enumerate(records):
        owner = str(record.get("canonical_id") or f"sources[{index}]")
        missing = {
            "canonical_id",
            "display_code",
            "display_name",
            "source_family",
            "source_kind",
            "source_identifier",
            "celex",
            "language",
            "official_eurlex_url",
            "oj_expression_uri",
            "fmx4_manifestation_uri",
            "source_url",
            "version_policy",
            "document_policy",
            "expected_limitation_id",
            "source_metadata",
        } - set(record)
        if missing:
            errors.append(f"{owner}: EU neighbor source missing fields {sorted(missing)}")
        canonical_id = record.get("canonical_id")
        if isinstance(canonical_id, str):
            if canonical_id in seen_canonical_ids:
                errors.append(f"duplicate EU neighbor canonical_id {canonical_id}")
            seen_canonical_ids.add(canonical_id)
        celex = record.get("celex")
        if not _valid_celex(celex):
            errors.append(f"{owner}: invalid CELEX {celex}")
        else:
            if celex in seen_celexes:
                errors.append(f"duplicate EU neighbor CELEX {celex}")
            seen_celexes.add(str(celex))
            if celex not in seed_celexes:
                errors.append(f"CELEX {celex} is not present in privacy scope seed")
        if record.get("source_family") != "eur-lex-cellar" or record.get("source_kind") != "eur-lex-cellar":
            errors.append(f"{owner}: EU neighbor source must use eur-lex-cellar")
        if record.get("language") != "de":
            errors.append(f"{owner}: EU neighbor language must be de")
        if record.get("source_identifier") != f"CELEX:{celex}":
            errors.append(f"{owner}: source_identifier must be CELEX:{celex}")
        if not _https(record.get("official_eurlex_url")) or not _https(record.get("source_url")):
            errors.append(f"{owner}: official URLs must be HTTPS")
        for uri_field in ("oj_expression_uri", "fmx4_manifestation_uri"):
            if not _https(record.get(uri_field)):
                errors.append(f"{owner}: {uri_field} must be HTTPS")
        metadata = record.get("source_metadata")
        if not isinstance(metadata, dict):
            errors.append(f"{owner}: source_metadata must be an object")
        else:
            missing_metadata = {"celex", "cellar_work", "expression", "language", "document"} - set(metadata)
            if missing_metadata:
                errors.append(f"{owner}: source_metadata missing fields {sorted(missing_metadata)}")
            if metadata.get("celex") != celex:
                errors.append(f"{owner}: source_metadata.celex must match CELEX {celex}")
            for field in ("cellar_work", "expression", "document"):
                value = metadata.get(field)
                if isinstance(value, str) and (value.startswith("fixture-") or value.startswith("pending-")):
                    errors.append(f"{owner}: placeholder source_metadata.{field} is not allowed")
            if metadata.get("expression") != "0004.02":
                errors.append(f"{owner}: source_metadata.expression must be 0004.02")
            if metadata.get("language") != "de":
                errors.append(f"{owner}: source_metadata.language must be de")
            if metadata.get("document") != "DOC_1":
                errors.append(f"{owner}: source_metadata.document must be DOC_1")
            cellar_work = metadata.get("cellar_work")
            expression = metadata.get("expression")
            document = metadata.get("document")
            expected_source_url = (
                f"https://publications.europa.eu/resource/cellar/{cellar_work}.{expression}/{document}"
                if all(isinstance(value, str) for value in (cellar_work, expression, document))
                else None
            )
            if record.get("source_url") != expected_source_url:
                errors.append(
                    f"{owner}: source_url must be official Publications/Cellar DOC_1 URL matching Cellar metadata"
                )
            seed_limitation = _seed_limitation_for_celex(seed, celex) if isinstance(celex, str) else None
            if seed_limitation is not None:
                seed_mappings = {
                    "work": cellar_work,
                    "expression": expression,
                    "document": document,
                    "source_url": record.get("source_url"),
                    "oj_expression_uri": record.get("oj_expression_uri"),
                    "fmx4_manifestation_uri": record.get("fmx4_manifestation_uri"),
                }
                for field, expected in seed_mappings.items():
                    actual = seed_limitation.get(field)
                    if actual != expected:
                        errors.append(
                            f"{owner}: seed limitation {field} {actual} does not match source metadata {expected}"
                        )
    missing_config = MINIMUM_EU_NEIGHBOR_CELEXS - seen_celexes
    for celex in sorted(missing_config):
        errors.append(f"configured EU neighbor CELEX {celex} is missing")
    return errors


def build_eu_neighbor_source_spec(record: dict[str, Any]) -> SourceSpec:
    return SourceSpec(
        canonical_id=record["canonical_id"],
        display_code=record["display_code"],
        source_kind="eur-lex-cellar",
        source_identifier=record["source_identifier"],
        index_url=None,
        source_url=record["source_url"],
        metadata=dict(record["source_metadata"]),
    )


def build_eu_neighbor_law(record: dict[str, Any], *, norm_count: int) -> dict[str, Any]:
    return {
        "canonical_id": record["canonical_id"],
        "display_code": record["display_code"],
        "display_name": record["display_name"],
        "source": eu_neighbor_source_metadata(
            record, content_hash="fixture-content", retrieved_at="2026-05-15T00:00:00Z"
        ),
        "aliases": [record["display_code"], record["canonical_id"], record["celex"]],
        "norm_count": norm_count,
    }


def eu_neighbor_source_metadata(record: dict[str, Any], *, content_hash: str, retrieved_at: str) -> dict[str, Any]:
    return {
        "source_kind": "eur-lex-cellar",
        "source_identifier": record["source_identifier"],
        "source_url": record["source_url"],
        "retrieved_at": retrieved_at,
        "stand_date": None,
        "stand_date_status": "official",
        "content_hash": content_hash,
        "source_metadata": dict(record["source_metadata"]),
    }


def parse_eu_neighbor_fixture(xml_path: Path, record: dict[str, Any]) -> list[dict[str, Any]]:
    content = xml_path.read_bytes()
    source = eu_neighbor_source_metadata(
        record,
        content_hash=hashlib.sha256(content).hexdigest(),
        retrieved_at="2026-05-15T00:00:00Z",
    )
    return parse_eurlex_act_xml(
        xml_path,
        {"canonical_id": record["canonical_id"]},
        source,
        error_label=f"EU neighbor CELEX {record['celex']}",
    )


def eu_neighbor_source_limitation(
    record: dict[str, Any],
    *,
    terminal_state: str,
    reason: str,
    details: dict[str, Any],
    retrieved_at: str,
) -> dict[str, Any]:
    limitation = {
        "limitation_id": record["expected_limitation_id"],
        "source_family": "eur-lex-cellar",
        "source_id": f"eur-lex-cellar:{record['celex']}",
        "celex": record["celex"],
        "language": record["language"],
        "official_eurlex_url": record["official_eurlex_url"],
        "work": record["source_metadata"]["cellar_work"],
        "expression": record["source_metadata"]["expression"],
        "document": record["source_metadata"]["document"],
        "version_policy": record["version_policy"],
        "terminal_state": terminal_state,
        "source_url": record["source_url"],
        "retrieved_at": retrieved_at,
        "reason": reason,
        "details": details,
    }
    if terminal_state == "source_unavailable":
        limitation["retryable"] = False
        limitation["error_code"] = details.get("error_code", "source_unavailable")
    elif terminal_state == "unsupported_format":
        limitation["content_type"] = details.get("content_type", "application/octet-stream")
    elif terminal_state == "parse_failed":
        limitation["parser_version"] = details.get("parser_version", "eurlex-neighbor-fixture")
        limitation["diagnostic_text"] = details.get("diagnostic_text", reason)
    elif terminal_state == "excluded_by_policy":
        limitation["policy_reason"] = details.get("policy_reason", "excluded_by_policy")
        limitation["policy_reference"] = details.get("policy_reference", "full-privacy-corpus-phase-7")
        limitation["decided_at"] = retrieved_at
    return limitation


def _seed_eu_celexes(seed: dict[str, Any]) -> set[str]:
    celexes: set[str] = set()
    for limitation in seed.get("source_limitations", []):
        if isinstance(limitation, dict) and limitation.get("source_family") == "eur-lex-cellar":
            celex = limitation.get("celex")
            if isinstance(celex, str):
                celexes.add(celex)
    targets = seed.get("official_targets")
    if isinstance(targets, dict):
        for values in targets.values():
            if not isinstance(values, list):
                continue
            for target in values:
                if isinstance(target, dict) and target.get("source_family") == "eur-lex-cellar":
                    celex = target.get("celex")
                    if isinstance(celex, str):
                        celexes.add(celex)
    return celexes


def _seed_limitation_for_celex(seed: dict[str, Any], celex: str) -> dict[str, Any] | None:
    for limitation in seed.get("source_limitations", []):
        if (
            isinstance(limitation, dict)
            and limitation.get("source_family") == "eur-lex-cellar"
            and limitation.get("celex") == celex
        ):
            return limitation
    return None


def _valid_celex(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"3\d{4}[A-Z]\d{4}", value) is not None


def _https(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://")
