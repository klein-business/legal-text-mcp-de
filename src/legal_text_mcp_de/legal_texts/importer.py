# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from .errors import source_unavailable
from .sources import SOURCE_SPECS, SourceSpec


Fetch = Callable[[str], tuple[int, dict[str, str], bytes]]


@dataclass
class RawSnapshotEntry:
    snapshot_id: str
    canonical_id: str
    source: dict
    raw_path: str
    bytes: int


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def default_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "legal-text-mcp-de/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.status, {k.lower(): v for k, v in response.headers.items()}, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {k.lower(): v for k, v in exc.headers.items()}, exc.read()


def sha256_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def source_metadata(spec: SourceSpec, content: bytes, retrieved_at: str) -> dict:
    stand_status = "not_exposed"
    return {
        "source_kind": spec.source_kind,
        "source_identifier": spec.source_identifier,
        "source_url": spec.source_url,
        "retrieved_at": retrieved_at,
        "stand_date": None,
        "stand_date_status": stand_status,
        "stand_date_issue": None,
        "content_hash": sha256_bytes(content),
        "source_metadata": spec.metadata or {},
        "known_issues": [],
    }


def probe_source(spec: SourceSpec, fetch: Fetch = default_fetch) -> dict:
    urls = [url for url in [spec.index_url, spec.source_url] if url]
    results = []
    for url in urls:
        status, headers, body = fetch(url)
        if status != 200:
            raise source_unavailable(
                f"Source URL unavailable: {url}",
                {"url": url, "status": status},
                {"source_kind": spec.source_kind, "source_identifier": spec.source_identifier},
            )
        results.append(
            {
                "url": url,
                "status": status,
                "content_type": headers.get("content-type", ""),
                "bytes": len(body),
                "sha256": sha256_bytes(body),
            }
        )
    return {"canonical_id": spec.canonical_id, "results": results}


def probe_known_invalid(fetch: Fetch = default_fetch) -> list[dict]:
    results: list[dict] = []
    for spec in SOURCE_SPECS.values():
        for url in spec.invalid_urls:
            status, headers, body = fetch(url)
            results.append(
                {
                    "canonical_id": spec.canonical_id,
                    "url": url,
                    "expected_status": 404,
                    "status": status,
                    "content_type": headers.get("content-type", ""),
                    "bytes": len(body),
                }
            )
    return results


def validate_dsgvo_doc2(content: bytes, content_type: str = "") -> None:
    validate_eurlex_german_act_xml(content, celex="32016R0679", content_type=content_type, label="DSGVO Cellar DOC_2")


def validate_eurlex_german_act_xml(
    content: bytes,
    *,
    celex: str,
    content_type: str = "",
    label: str | None = None,
) -> None:
    text = content.decode("utf-8", errors="replace")
    missing = [
        marker
        for marker in ("<LG.DOC>DE</LG.DOC>", "<ACT", "<ARTICLE")
        if marker not in text
    ]
    if missing:
        raise source_unavailable(
            f"{label or celex} does not look like German article XML.",
            {"celex": celex, "missing_markers": missing, "content_type": content_type},
        )


def import_snapshot(
    snapshot_dir: Path,
    *,
    snapshot_id: str | None = None,
    fetch: Fetch = default_fetch,
) -> dict:
    snapshot = snapshot_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    root = snapshot_dir / snapshot
    root.mkdir(parents=True, exist_ok=True)
    retrieved_at = utc_now()
    entries: list[RawSnapshotEntry] = []

    for spec in SOURCE_SPECS.values():
        status, headers, body = fetch(spec.source_url)
        if status != 200:
            raise source_unavailable(
                f"Source URL unavailable: {spec.source_url}",
                {"url": spec.source_url, "status": status},
            )
        if spec.canonical_id == "dsgvo_eu_2016_679":
            validate_dsgvo_doc2(body, headers.get("content-type", ""))
        suffix = ".xml" if spec.source_kind == "eur-lex-cellar" else ".zip"
        raw_name = f"{spec.canonical_id}{suffix}"
        raw_path = root / raw_name
        raw_path.write_bytes(body)
        entries.append(
            RawSnapshotEntry(
                snapshot_id=snapshot,
                canonical_id=spec.canonical_id,
                source=source_metadata(spec, body, retrieved_at),
                raw_path=str(raw_path),
                bytes=len(body),
            )
        )

    manifest = {
        "dataset_id": snapshot,
        "snapshot_id": snapshot,
        "created_at": retrieved_at,
        "hash_algorithm": "sha256",
        "entries": [asdict(entry) for entry in entries],
        "validation": {"state": "ready", "entry_count": len(entries)},
    }
    (root / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def diff_manifests(old: dict, new: dict) -> dict:
    old_hashes = {entry["canonical_id"]: entry["source"]["content_hash"] for entry in old.get("entries", [])}
    new_hashes = {entry["canonical_id"]: entry["source"]["content_hash"] for entry in new.get("entries", [])}
    changed = sorted(law_id for law_id, content_hash in new_hashes.items() if old_hashes.get(law_id) != content_hash)
    removed = sorted(set(old_hashes) - set(new_hashes))
    added = sorted(set(new_hashes) - set(old_hashes))
    return {"added": added, "removed": removed, "changed": changed}
