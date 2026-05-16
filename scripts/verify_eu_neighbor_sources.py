#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from collections.abc import Callable
from io import BytesIO
from pathlib import Path
from typing import Any

from legal_text_mcp_de.legal_texts.eu_neighbors import (  # type: ignore[import-untyped]
    eu_neighbor_source_limitation,
    eu_neighbor_source_metadata,
    load_eu_neighbor_source_records,
    parse_eu_neighbor_fixture,
    validate_eu_neighbor_source_records,
)
from legal_text_mcp_de.legal_texts.eurlex_xml import parse_eurlex_act_xml  # type: ignore[import-untyped]
from legal_text_mcp_de.legal_texts.relationships import load_privacy_scope_seed  # type: ignore[import-untyped]

Fetch = Callable[[str], tuple[int, dict[str, str], bytes]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate bounded EU neighbor source evidence.")
    parser.add_argument("--seed", required=True, help="privacy_scope_seed.v1.json path.")
    parser.add_argument("--sources", required=True, help="eu_neighbor_sources.v1.json path.")
    parser.add_argument("--output", required=True, help="Path where eu-neighbor-sources.v1 evidence should be written.")
    parser.add_argument(
        "--fixture-dir", help="Optional fixture directory with <canonical_id>.xml or known sample XML files."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    seed = load_privacy_scope_seed(Path(args.seed))
    records = load_eu_neighbor_source_records(Path(args.sources))
    artifact = build_artifact(records, seed, fixture_dir=Path(args.fixture_dir) if args.fixture_dir else None)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if artifact["validation_errors"]:
        for error in artifact["validation_errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


def build_artifact(
    records: list[dict[str, Any]], seed: dict[str, Any], *, fixture_dir: Path | None, fetch: Fetch | None = None
) -> dict[str, Any]:
    errors = validate_eu_neighbor_source_records(records, seed)
    source_results = []
    imported = 0
    limited = 0
    fetch = fetch or default_fetch
    for record in records:
        fixture_path = _fixture_path(record, fixture_dir)
        if fixture_path and fixture_path.exists():
            try:
                norms = parse_eu_neighbor_fixture(fixture_path, record)
            except ValueError as exc:
                limited += 1
                source_results.append(
                    {
                        "celex": record["celex"],
                        "canonical_id": record["canonical_id"],
                        "terminal_state": "parse_failed",
                        "validation_error": str(exc),
                    }
                )
                errors.append(f"{record['celex']}: fixture parse failed: {exc}")
            else:
                imported += 1
                source_results.append(
                    {
                        "celex": record["celex"],
                        "canonical_id": record["canonical_id"],
                        "language": record["language"],
                        "terminal_state": "imported",
                        "norm_count": len(norms),
                        "generated_norm_ids": [norm["canonical_id"] for norm in norms],
                        "source_url": record["source_url"],
                        "version_policy": record["version_policy"],
                    }
                )
            continue

        try:
            status, headers, body = fetch(record["source_url"])
        except Exception as exc:  # pragma: no cover - exact urllib exception type is environment-dependent.
            status, headers, body = 0, {}, str(exc).encode("utf-8", errors="replace")
        content_type = headers.get("content-type", headers.get("Content-Type", ""))
        content_sha256 = hashlib.sha256(body).hexdigest()
        if status != 200:
            limited += 1
            limitation = eu_neighbor_source_limitation(
                record,
                terminal_state="source_unavailable",
                reason=f"official source returned status {status}",
                details={"http_status": status, "content_type": content_type, "error_code": f"http_{status}"},
                retrieved_at="2026-05-15T00:00:00Z",
            )
            source_results.append(
                _limited_result(record, limitation, content_type=content_type, content_sha256=content_sha256)
            )
            continue
        try:
            norms = _parse_official_payload(record, body, content_type, content_sha256)
        except UnsupportedFormat as exc:
            limited += 1
            limitation = eu_neighbor_source_limitation(
                record,
                terminal_state="unsupported_format",
                reason=str(exc),
                details={"content_type": content_type},
                retrieved_at="2026-05-15T00:00:00Z",
            )
            source_results.append(
                _limited_result(record, limitation, content_type=content_type, content_sha256=content_sha256)
            )
        except ValueError as exc:
            limited += 1
            limitation = eu_neighbor_source_limitation(
                record,
                terminal_state="parse_failed",
                reason="official FMX4 payload could not be parsed",
                details={"content_type": content_type, "diagnostic_text": str(exc)},
                retrieved_at="2026-05-15T00:00:00Z",
            )
            source_results.append(
                _limited_result(record, limitation, content_type=content_type, content_sha256=content_sha256)
            )
        else:
            imported += 1
            source_results.append(
                {
                    "celex": record["celex"],
                    "canonical_id": record["canonical_id"],
                    "language": record["language"],
                    "terminal_state": "imported",
                    "norm_count": len(norms),
                    "generated_norm_ids": [norm["canonical_id"] for norm in norms],
                    "source_url": record["source_url"],
                    "version_policy": record["version_policy"],
                    "content_type": content_type,
                    "content_sha256": content_sha256,
                }
            )
    return {
        "schema_version": "eu-neighbor-sources.v1",
        "seeded_celex": sorted(record["celex"] for record in records),
        "counts": {
            "seeded_sources": len(records),
            "imported": imported,
            "limited": limited,
        },
        "source_results": source_results,
        "validation_errors": errors,
    }


class UnsupportedFormat(ValueError):
    pass


def default_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "legal-text-mcp-de/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {key.lower(): value for key, value in exc.headers.items()}, exc.read()


def _parse_official_payload(
    record: dict[str, Any], body: bytes, content_type: str, content_sha256: str
) -> list[dict[str, Any]]:
    lower_content_type = content_type.lower()
    if body.startswith(b"PK\x03\x04") or "zip" in lower_content_type:
        xml_bytes = _extract_act_xml_from_zip(body)
    elif b"<ACT" in body and b"<LG.DOC>DE</LG.DOC>" in body:
        xml_bytes = body
    else:
        raise UnsupportedFormat("official source response is neither ZIP nor German act XML")
    with tempfile.TemporaryDirectory() as tmp:
        xml_path = Path(tmp) / "act.xml"
        xml_path.write_bytes(xml_bytes)
        source = eu_neighbor_source_metadata(
            record,
            content_hash=content_sha256,
            retrieved_at="2026-05-15T00:00:00Z",
        )
        result: list[dict[str, Any]] = parse_eurlex_act_xml(
            xml_path,
            {"canonical_id": record["canonical_id"]},
            source,
            error_label=f"EU neighbor CELEX {record['celex']}",
        )
        return result


def _extract_act_xml_from_zip(body: bytes) -> bytes:
    try:
        with zipfile.ZipFile(BytesIO(body)) as archive:
            for name in archive.namelist():
                if not name.lower().endswith(".xml"):
                    continue
                content = archive.read(name)
                if b"<LG.DOC>DE</LG.DOC>" in content and b"<ACT" in content and b"<ARTICLE" in content:
                    return content
    except zipfile.BadZipFile as exc:
        raise UnsupportedFormat("official source response is not a readable ZIP") from exc
    raise ValueError("No parseable German act XML found in official FMX4 ZIP")


def _limited_result(
    record: dict[str, Any], limitation: dict[str, Any], *, content_type: str, content_sha256: str
) -> dict[str, Any]:
    return {
        "celex": record["celex"],
        "canonical_id": record["canonical_id"],
        "language": record["language"],
        "terminal_state": limitation["terminal_state"],
        "source_url": record["source_url"],
        "version_policy": record["version_policy"],
        "content_type": content_type,
        "content_sha256": content_sha256,
        "limitation_id": limitation["limitation_id"],
        "limitation": limitation,
    }


def _fixture_path(record: dict[str, Any], fixture_dir: Path | None) -> Path | None:
    if fixture_dir is None:
        return None
    candidates = [
        fixture_dir / f"{record['canonical_id']}.xml",
        fixture_dir / f"{record['celex']}.xml",
    ]
    if record["celex"] == "32024R1689":
        candidates.append(fixture_dir / "ai_act_de_sample.xml")
    if record["celex"] == "32023R2854":
        candidates.append(fixture_dir / "data_act_de_sample.xml")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


if __name__ == "__main__":
    raise SystemExit(main())
