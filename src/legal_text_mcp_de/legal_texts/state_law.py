# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import html
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urljoin

from .gii_xml import _subdivisions
from .manifest import validate_corpus_manifest
from .state_law_inventory import validate_state_law_inventory
from .validation import validate_generated_package, validate_laws, validate_norms


STATE_LAW_ADAPTER_SCHEMA_VERSION = "state-law-adapter-gate.v1"
STATE_LAW_ADAPTER_VERSION = "state-law-html-adapter.v1"
ELIGIBLE_ADAPTER_CLASSES = {"machine_readable", "stable_html"}
NOISE_TAGS = {"script", "style", "noscript", "nav", "header", "footer", "aside", "select", "option"}
BLOCK_TAGS = {
    "address",
    "article",
    "blockquote",
    "br",
    "dd",
    "div",
    "dl",
    "dt",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "li",
    "main",
    "ol",
    "p",
    "section",
    "table",
    "td",
    "th",
    "tr",
    "ul",
}
FALLBACK_HEADING_RE = re.compile(
    r"(?m)(?:^|\n)\s*(?:(?P<par_symbol>§{1,2})\s*(?P<par>\d+[a-z]?)|(?P<art_symbol>Art\.?|Artikel)\s*(?P<art>\d+[a-z]?))\b(?P<title>[^\n]*)",
    re.IGNORECASE,
)
ABS_MARKER_RE = re.compile(r"\(\d+\)")
PORTAL_CHROME_TERMS = {
    "detailansicht",
    "drucken",
    "hilfe",
    "inhaltsübersicht",
    "navigation",
    "portalansicht",
    "pragraph",
    "reiter",
    "suche",
    "teilen",
    "trefferliste",
}
PORTAL_CHROME_PHRASES = (
    "Einzelnorm",
    "nach oben",
    "Mehr Paragraph",
    "ausdrucken",
    "Link kopieren",
    "Link kopiert",
    "Pragraph",
    "Zum Textanfang",
    "Textanfang",
)
LEGAL_SIGNAL_TERMS = {
    "absatz",
    "behörde",
    "behörden",
    "bestimmung",
    "daten",
    "gesetz",
    "gilt",
    "öffentliche",
    "personenbezogene",
    "stelle",
    "stellen",
    "verarbeitung",
    "vorschrift",
}

Fetch = Callable[[str], tuple[int, dict[str, str], bytes]]


@dataclass
class ParsedStateLaw:
    law: dict[str, Any]
    norms: list[dict[str, Any]]
    manifest_record: dict[str, Any]


@dataclass
class StateLawAdapterResult:
    package_dir: Path
    laws: list[dict[str, Any]]
    norms: list[dict[str, Any]]
    manifest: dict[str, Any]
    source_limitations: list[dict[str, Any]]
    terminal_state_counts: dict[str, int]
    source_outcomes: dict[str, dict[str, Any]]
    validation_errors: list[str]


def eligible_state_law_records(inventory: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        record
        for record in inventory.get("states", [])
        if isinstance(record, dict) and record.get("adapter_class") in ELIGIBLE_ADAPTER_CLASSES
    ]


def parse_state_law_html(
    body: bytes | str,
    record: dict[str, Any],
    *,
    source_url: str,
    retrieved_at: str,
    original_source_url: str | None = None,
) -> ParsedStateLaw:
    text = body.decode("utf-8", errors="replace") if isinstance(body, bytes) else body
    parser = _StateLawHtmlParser()
    parser.feed(text)
    parser.close()
    visible = _visible_text(text)
    title = _select_law_title(record, parser.title or visible.title, visible.text)
    law_id = record["law_id"]
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    parser_mode = "synthetic_markers" if parser.norms else "official_html_fallback"
    source = _state_law_source_metadata(
        record,
        source_url,
        content_hash,
        retrieved_at,
        original_source_url=original_source_url,
        parser_mode=parser_mode,
    )
    norms: list[dict[str, Any]] = []
    norm_items = parser.norms or _fallback_norm_items(visible.text)
    for item in norm_items:
        unit = item["unit"]
        value = item["value"].lower()
        norm_id = f"{unit}:{value}"
        norm_text = _sanitize_portal_chrome_text(item["text"])
        if not norm_text:
            continue
        norms.append({
            "canonical_id": f"{law_id}/{norm_id}",
            "law_id": law_id,
            "norm_id": norm_id,
            "unit": unit,
            "value": value,
            "title": item.get("title"),
            "text": norm_text,
            "status": "active",
            "url": f"{source_url}#{norm_id.replace(':', '-')}",
            "source": source,
            "subdivisions": _subdivisions(norm_text),
        })
    if not norms:
        raise ValueError("stable HTML adapter found no parseable norm records")

    law = {
        "canonical_id": law_id,
        "display_code": f"{record['state_code']} LDSG",
        "display_name": title,
        "source": source,
        "aliases": sorted({record["state_code"], record["state_code"].lower(), record["law_slug"], law_id, title}),
        "norm_count": len(norms),
        "stand_date": None,
    }
    manifest_record = {
        **_base_manifest_source(record),
        "terminal_state": "imported",
        "canonical_id": law_id,
        "source_url": source_url,
        "original_source_url": original_source_url or source_url,
        "content_sha256": content_hash,
        "retrieved_at": retrieved_at,
        "parser_version": STATE_LAW_ADAPTER_VERSION,
        "generated_law_ids": [law_id],
        "generated_norm_ids": [norm["canonical_id"] for norm in norms],
    }
    if original_source_url and source_url != original_source_url:
        manifest_record["resolved_source_url"] = source_url
    return ParsedStateLaw(law=law, norms=norms, manifest_record=manifest_record)


def run_state_law_adapters(
    inventory: dict[str, Any],
    limitations: list[dict[str, Any]],
    *,
    package_dir: Path,
    retrieved_at: str,
    fetch: Fetch | None = None,
) -> StateLawAdapterResult:
    fetch = fetch or default_fetch
    package_dir.mkdir(parents=True, exist_ok=True)
    validation_errors = validate_state_law_inventory(inventory, limitations)
    limitations_by_id = {
        limitation.get("limitation_id"): limitation
        for limitation in limitations
        if isinstance(limitation.get("limitation_id"), str)
    }
    laws: list[dict[str, Any]] = []
    norms: list[dict[str, Any]] = []
    source_limitations: list[dict[str, Any]] = []
    discovered_sources: list[dict[str, Any]] = []
    source_outcomes: dict[str, dict[str, Any]] = {}
    terminal_state_counts: Counter[str] = Counter()

    for record in inventory.get("states", []):
        if not isinstance(record, dict):
            continue
        if record.get("adapter_class") == "limitation_only":
            limitation = limitations_by_id.get(record.get("source_limitation_id"))
            if limitation is None:
                continue
            source_limitations.append(limitation)
            manifest_record = {**_base_manifest_source(record), **_manifest_failure_fields(limitation)}
            discovered_sources.append(manifest_record)
            terminal_state_counts[limitation["terminal_state"]] += 1
            source_outcomes[record["law_id"]] = {
                "terminal_state": limitation["terminal_state"],
                "state_code": record.get("state_code"),
                "law_id": record.get("law_id"),
                "limitation_id": limitation.get("limitation_id"),
            }
            continue
        if record.get("adapter_class") not in ELIGIBLE_ADAPTER_CLASSES:
            continue
        outcome = _run_one_adapter(record, retrieved_at=retrieved_at, fetch=fetch)
        source_outcomes[record["law_id"]] = outcome
        terminal_state_counts[outcome["terminal_state"]] += 1
        discovered_sources.append(outcome["manifest_record"])
        if outcome.get("law") is not None:
            laws.append(outcome["law"])
            norms.extend(outcome["norms"])
        if outcome.get("limitation") is not None:
            source_limitations.append(outcome["limitation"])

    manifest = _build_manifest(discovered_sources, source_limitations, retrieved_at)
    _write_generated_package(
        package_dir=package_dir,
        laws=sorted(laws, key=lambda item: item["canonical_id"]),
        norms=sorted(norms, key=lambda item: item["canonical_id"]),
        manifest=manifest,
        source_limitations=sorted(source_limitations, key=lambda item: item["limitation_id"]),
        retrieved_at=retrieved_at,
    )
    validation_errors.extend(
        validate_laws(laws)
        + validate_norms(norms, require_generated_container_schema=True)
        + _validate_no_portal_chrome(norms)
        + [f"manifest: {error}" for error in validate_corpus_manifest(manifest, require_terminal_states=True)]
        + [f"package: {error}" for error in validate_generated_package(package_dir, require_search_index=True)]
    )
    return StateLawAdapterResult(
        package_dir=package_dir,
        laws=laws,
        norms=norms,
        manifest=manifest,
        source_limitations=source_limitations,
        terminal_state_counts=dict(sorted(terminal_state_counts.items())),
        source_outcomes=source_outcomes,
        validation_errors=validation_errors,
    )


def build_state_law_adapter_gate_artifact(
    inventory: dict[str, Any],
    limitations: list[dict[str, Any]],
    *,
    package_dir: Path,
    retrieved_at: str,
    fetch: Fetch | None = None,
) -> dict[str, Any]:
    result = run_state_law_adapters(
        inventory,
        limitations,
        package_dir=package_dir,
        retrieved_at=retrieved_at,
        fetch=fetch,
    )
    eligible_count = len(eligible_state_law_records(inventory))
    return {
        "schema_version": STATE_LAW_ADAPTER_SCHEMA_VERSION,
        "generated_at": retrieved_at,
        "parser_version": STATE_LAW_ADAPTER_VERSION,
        "counts": {
            "inventory_states": len(inventory.get("states", [])),
            "eligible_sources": eligible_count,
            "limitation_only_sources": sum(
                1 for record in inventory.get("states", []) if isinstance(record, dict) and record.get("adapter_class") == "limitation_only"
            ),
            "imported": result.terminal_state_counts.get("imported", 0),
            "source_unavailable": result.terminal_state_counts.get("source_unavailable", 0),
            "unsupported_format": result.terminal_state_counts.get("unsupported_format", 0),
            "parse_failed": result.terminal_state_counts.get("parse_failed", 0),
            "laws": len(result.laws),
            "norms": len(result.norms),
            "source_limitations": len(result.source_limitations),
        },
        "terminal_state_coverage": result.terminal_state_counts,
        "source_outcomes": result.source_outcomes,
        "generated_package": {
            "path": str(package_dir),
            "sha256": _hash_package(package_dir),
        },
        "validation_errors": result.validation_errors,
    }


def write_state_law_adapter_gate_artifact(artifact: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def default_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "legal-text-mcp-de/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {key.lower(): value for key, value in exc.headers.items()}, exc.read()


def _run_one_adapter(record: dict[str, Any], *, retrieved_at: str, fetch: Fetch) -> dict[str, Any]:
    source = record["official_sources"][0]
    original_source_url = source["url"]
    base_manifest = _base_manifest_source(record)
    try:
        status, headers, body, source_url = _fetch_with_one_meta_refresh(original_source_url, fetch)
    except Exception as exc:
        limitation = _source_limitation(
            record,
            "source_unavailable",
            source_url=original_source_url,
            retrieved_at=retrieved_at,
            reason="official state-law source could not be fetched",
            original_source_url=original_source_url,
            retryable=True,
            error_code="fetch_exception",
            diagnostic=str(exc),
        )
        return _failure_outcome(base_manifest, limitation)
    content_type = headers.get("content-type", headers.get("Content-Type", ""))
    content_sha256 = hashlib.sha256(body).hexdigest()
    if not isinstance(status, int) or status < 200 or status >= 400:
        limitation = _source_limitation(
            record,
            "source_unavailable",
            source_url=source_url,
            retrieved_at=retrieved_at,
            reason=f"official state-law source returned status {status}",
            original_source_url=original_source_url,
            retryable=True,
            http_status=status if isinstance(status, int) else None,
            error_code=f"http_{status}" if isinstance(status, int) else "bad_status",
            content_sha256=content_sha256,
        )
        return _failure_outcome(base_manifest, limitation)
    if "html" not in content_type.lower():
        limitation = _source_limitation(
            record,
            "unsupported_format",
            source_url=source_url,
            retrieved_at=retrieved_at,
            reason="official state-law source is not HTML",
            original_source_url=original_source_url,
            content_type=content_type,
            content_sha256=content_sha256,
        )
        return _failure_outcome(base_manifest, limitation)
    try:
        parsed = parse_state_law_html(
            body,
            record,
            source_url=source_url,
            retrieved_at=retrieved_at,
            original_source_url=original_source_url,
        )
    except ValueError as exc:
        limitation = _source_limitation(
            record,
            "parse_failed",
            source_url=source_url,
            retrieved_at=retrieved_at,
            reason="stable HTML adapter could not parse official source",
            original_source_url=original_source_url,
            parser_version=STATE_LAW_ADAPTER_VERSION,
            diagnostic=str(exc),
            content_fetched=True,
            content_sha256=content_sha256,
        )
        return _failure_outcome(base_manifest, limitation)
    return {
        "terminal_state": "imported",
        "state_code": record.get("state_code"),
        "law_id": record.get("law_id"),
        "original_source_url": original_source_url,
        "resolved_source_url": source_url,
        "manifest_record": parsed.manifest_record,
        "law": parsed.law,
        "norms": parsed.norms,
        "limitation": None,
    }


def _failure_outcome(base_manifest: dict[str, Any], limitation: dict[str, Any]) -> dict[str, Any]:
    details = limitation.get("details") if isinstance(limitation.get("details"), dict) else {}
    return {
        "terminal_state": limitation["terminal_state"],
        "state_code": limitation.get("state_code"),
        "law_id": limitation.get("law_id"),
        "original_source_url": details.get("original_source_url", limitation.get("source_url")),
        "resolved_source_url": details.get("resolved_source_url", limitation.get("source_url")),
        "manifest_record": {**base_manifest, **_manifest_failure_fields(limitation)},
        "law": None,
        "norms": [],
        "limitation": limitation,
    }


def _state_law_source_metadata(
    record: dict[str, Any],
    source_url: str,
    content_hash: str,
    retrieved_at: str,
    *,
    original_source_url: str | None = None,
    parser_mode: str,
) -> dict[str, Any]:
    official_source_url = original_source_url or source_url
    source_metadata = {
        "state_code": record["state_code"].lower(),
        "jurisdiction": record["state_name"],
        "official_source_url": official_source_url,
        "source_format": record["source_format"],
        "adapter_class": record["adapter_class"],
        "law_slug": record["law_slug"],
        "law_id": record["law_id"],
        "parser_version": STATE_LAW_ADAPTER_VERSION,
        "parser_mode": parser_mode,
        "original_source_url": official_source_url,
    }
    if source_url != official_source_url:
        source_metadata["resolved_source_url"] = source_url
    return {
        "source_kind": "state-law",
        "source_identifier": record["law_id"],
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "stand_date": None,
        "stand_date_status": "not_exposed",
        "content_hash": content_hash,
        "source_metadata": source_metadata,
        "known_issues": [],
    }


def _source_limitation(
    record: dict[str, Any],
    terminal_state: str,
    *,
    source_url: str,
    retrieved_at: str,
    reason: str,
    original_source_url: str | None = None,
    retryable: bool | None = None,
    http_status: int | None = None,
    error_code: str | None = None,
    content_type: str | None = None,
    content_sha256: str | None = None,
    parser_version: str | None = None,
    diagnostic: str | None = None,
    content_fetched: bool | None = None,
) -> dict[str, Any]:
    official_source_url = original_source_url or source_url
    limitation = {
        **_base_manifest_source(record),
        "limitation_id": f"lim-{record['state_code'].lower()}-{record['law_slug']}-{terminal_state.replace('_', '-')}",
        "law_id": record["law_id"],
        "terminal_state": terminal_state,
        "source_url": source_url,
        "retrieved_at": retrieved_at,
        "reason": reason,
        "details": {
            "phase": "phase-9",
            "implementation_evidence": True,
            "adapter_class": record.get("adapter_class"),
            "original_source_url": official_source_url,
            "resolved_source_url": source_url,
        },
    }
    if retryable is not None:
        limitation["retryable"] = retryable
    if http_status is not None:
        limitation["http_status"] = http_status
    if error_code is not None:
        limitation["error_code"] = error_code
    if content_type is not None:
        limitation["content_type"] = content_type
    if content_sha256 is not None:
        limitation["content_sha256"] = content_sha256
    if parser_version is not None:
        limitation["parser_version"] = parser_version
    if diagnostic is not None:
        limitation["diagnostic"] = diagnostic
        limitation["details"]["diagnostic"] = diagnostic
    if content_fetched is not None:
        limitation["content_fetched"] = content_fetched
    return limitation


def _base_manifest_source(record: dict[str, Any]) -> dict[str, Any]:
    source_url = record["official_sources"][0]["url"] if record.get("official_sources") else record.get("source_url")
    return {
        "source_family": "state-law",
        "source_id": f"state-law:{record['state_code'].lower()}/{record['law_slug']}",
        "state_code": record["state_code"].lower(),
        "jurisdiction": record["state_name"],
        "official_source_url": source_url,
        "source_format": record["source_format"],
        "adapter_class": record["adapter_class"],
        "source_metadata": {
            "state_code": record["state_code"].lower(),
            "law_slug": record["law_slug"],
            "law_id": record["law_id"],
        },
    }


def _manifest_failure_fields(limitation: dict[str, Any]) -> dict[str, Any]:
    fields = dict(limitation)
    fields.pop("limitation_id", None)
    fields.pop("details", None)
    fields.pop("law_id", None)
    return fields


def _build_manifest(
    discovered_sources: list[dict[str, Any]],
    source_limitations: list[dict[str, Any]],
    retrieved_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "state-law-adapter-fixture",
        "package_id": f"state-law-adapter-fixture-{retrieved_at}",
        "created_at": retrieved_at,
        "validation_mode": "terminal",
        "generator": {"name": "state-law-adapter-fixture", "version": STATE_LAW_ADAPTER_VERSION},
        "parser_versions": {"state_law_html": STATE_LAW_ADAPTER_VERSION},
        "discovered_sources": discovered_sources,
        "canonical_ids": [
            {
                "canonical_id": source["canonical_id"],
                "source_family": "state-law",
                "source_id": source["source_id"],
                "state_code": source["state_code"],
            }
            for source in discovered_sources
            if source.get("terminal_state") == "imported"
        ],
        "relationship_sources": [],
        "source_limitations": source_limitations,
        "generated_package": {
            "schema_version": "generated-package.v1",
            "generated_at": retrieved_at,
            "record_counts": {
                "discovered_sources": len(discovered_sources),
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
        "dataset_id": "state-law-adapter-fixture",
        "package_id": f"state-law-adapter-fixture-{retrieved_at}",
        "generated_at": retrieved_at,
        "generator": {"name": "state-law-adapter-fixture", "version": STATE_LAW_ADAPTER_VERSION},
        "manifest_path": "manifest.json",
        "readiness_path": "readiness.json",
        "record_counts": {
            "laws": len(laws),
            "norms": len(norms),
            "relationships": 0,
            "source_limitations": len(source_limitations),
            "discovered_sources": len(manifest["discovered_sources"]),
            "imported_sources": sum(
                1 for source in manifest["discovered_sources"] if source.get("terminal_state") == "imported"
            ),
        },
        "content_hashes": {
            name: f"sha256:{_file_sha256(package_dir / name)}"
            for name in files
        },
        "validation_mode": "terminal",
        "source_families": ["state-law"],
    }
    (package_dir / "package.json").write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _hash_package(package_dir: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(package_dir.glob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clean_text(value: str) -> str:
    return " ".join(html.unescape(value).split())


def _fetch_with_one_meta_refresh(url: str, fetch: Fetch) -> tuple[int, dict[str, str], bytes, str]:
    status, headers, body = fetch(url)
    content_type = headers.get("content-type", headers.get("Content-Type", ""))
    if isinstance(status, int) and 200 <= status < 400 and "html" in content_type.lower():
        refresh_url = _meta_refresh_url(body, url)
        if refresh_url and refresh_url != url:
            next_status, next_headers, next_body = fetch(refresh_url)
            return next_status, next_headers, next_body, refresh_url
    return status, headers, body, url


def _meta_refresh_url(body: bytes, base_url: str) -> str | None:
    text = body.decode("utf-8", errors="replace")
    for match in re.finditer(r"<meta\b[^>]*>", text, flags=re.IGNORECASE):
        tag = match.group(0)
        if "refresh" not in tag.lower():
            continue
        content_match = re.search(r"""content\s*=\s*["']([^"']+)["']""", tag, flags=re.IGNORECASE)
        if not content_match:
            continue
        url_match = re.search(r"url\s*=\s*([^;]+)", content_match.group(1), flags=re.IGNORECASE)
        if not url_match:
            continue
        return urljoin(base_url, url_match.group(1).strip(" '\""))
    return None


@dataclass
class _VisibleText:
    title: str | None
    text: str


def _visible_text(text: str) -> _VisibleText:
    parser = _VisibleTextParser()
    parser.feed(text)
    parser.close()
    return _VisibleText(title=parser.title, text=parser.text)


def _fallback_norm_items(visible_text: str) -> list[dict[str, Any]]:
    matches = list(FALLBACK_HEADING_RE.finditer(visible_text))
    candidates_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for index, match in enumerate(matches):
        unit = "par" if match.group("par") else "art"
        value = (match.group("par") or match.group("art") or "").lower()
        title_tail = _clean_text(match.group("title") or "")
        segment_start = match.end()
        segment_end = matches[index + 1].start() if index + 1 < len(matches) else len(visible_text)
        segment = visible_text[segment_start:segment_end]
        title, prefix = _split_heading_tail(title_tail)
        norm_text = _sanitize_portal_chrome_text(f"{prefix} {segment}")
        key = (unit, value)
        if not _substantive_norm_text(norm_text):
            continue
        candidates_by_key.setdefault(key, []).append({"unit": unit, "value": value, "title": title, "text": norm_text})
    items: list[dict[str, Any]] = []
    for key in sorted(candidates_by_key, key=lambda item: (item[0], _sort_norm_value(item[1]))):
        best = max(candidates_by_key[key], key=_norm_candidate_score)
        items.append(best)
    return items


def _split_heading_tail(value: str) -> tuple[str | None, str]:
    match = ABS_MARKER_RE.search(value)
    if not match:
        return (value or None), ""
    return (value[:match.start()].strip() or None), value[match.start():]


def _substantive_norm_text(value: str) -> bool:
    if ABS_MARKER_RE.search(value) and len(value) >= 45:
        return True
    return len(value) >= 160 and bool(re.search(r"[.!?]", value))


def _select_law_title(record: dict[str, Any], page_title: str | None, visible_text: str) -> str:
    if page_title and not _portal_chrome_title(page_title):
        return _clean_text(page_title)
    legal_title = _legal_title_from_visible_text(record, visible_text)
    if legal_title:
        return legal_title
    return _inventory_law_title(record)


def _portal_chrome_title(value: str) -> bool:
    normalized = value.casefold()
    return any(
        term in normalized
        for term in (
            "vorschriftensystem",
            "detailansicht",
            "einzelnorm",
            "landesrecht",
            "rechtsprechung",
            "suchergebnis",
        )
    )


def _legal_title_from_visible_text(record: dict[str, Any], visible_text: str) -> str | None:
    slug_tokens = [token for token in record.get("law_slug", "").split("-") if len(token) > 3]
    for line in visible_text.splitlines():
        candidate = _clean_text(line)
        normalized = candidate.casefold()
        if not candidate or _portal_chrome_title(candidate):
            continue
        if "datenschutzgesetz" in normalized or (
            slug_tokens and sum(1 for token in slug_tokens if token.casefold() in normalized) >= min(2, len(slug_tokens))
        ):
            return candidate
    return None


def _inventory_law_title(record: dict[str, Any]) -> str:
    return " ".join(part.capitalize() for part in str(record.get("law_slug", "")).split("-") if part) or str(record["law_id"])


def _sanitize_portal_chrome_text(value: str) -> str:
    text = _clean_text(value)
    text = re.sub(r"\bMehr\s+Paragraph\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bParagraph\s+ausdrucken\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bausdrucken\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bParagraph\s+Link\s+kopieren\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bLink\s+kopieren\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bLink\s+kopiert\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bDer\s+Link\s+zum\s+Pragraph\s+wurde\s+kopiert\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bEinzelnorm(?:\s+nach oben)?\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bnach oben\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bZum\s+Textanfang\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bTextanfang\b", " ", text, flags=re.IGNORECASE)
    return _clean_text(text)


def _validate_no_portal_chrome(norms: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    for norm in norms:
        source = norm.get("source") if isinstance(norm.get("source"), dict) else {}
        if source.get("source_kind") != "state-law":
            continue
        norm_id = str(norm.get("canonical_id", "<unknown>"))
        text = norm.get("text")
        if isinstance(text, str):
            for phrase in _portal_chrome_hits(text):
                errors.append(f"{norm_id}: text contains portal chrome phrase '{phrase}'")
        for subdivision in norm.get("subdivisions") or []:
            if not isinstance(subdivision, dict):
                continue
            subdivision_text = subdivision.get("text")
            if not isinstance(subdivision_text, str):
                continue
            path = subdivision.get("path", "<unknown>")
            for phrase in _portal_chrome_hits(subdivision_text):
                errors.append(f"{norm_id}: subdivision {path} contains portal chrome phrase '{phrase}'")
    return errors


def _portal_chrome_hits(value: str) -> list[str]:
    normalized = value.casefold()
    return [phrase for phrase in PORTAL_CHROME_PHRASES if phrase.casefold() in normalized]


def _sort_norm_value(value: str) -> tuple[int, str]:
    match = re.fullmatch(r"(\d+)([a-z]?)", value)
    if not match:
        return (10_000, value)
    return (int(match.group(1)), match.group(2))


def _norm_candidate_score(candidate: dict[str, Any]) -> int:
    text = str(candidate.get("text") or "")
    normalized = text.casefold()
    score = min(len(text), 1200) // 20
    score += len(ABS_MARKER_RE.findall(text)) * 30
    score += len(re.findall(r"(?<=[.!?])\s+", text)) * 8
    score += sum(12 for term in LEGAL_SIGNAL_TERMS if term in normalized)
    score -= sum(45 for term in PORTAL_CHROME_TERMS if term.casefold() in normalized)
    if normalized.startswith("(1)"):
        score += 15
    if "hilfe - detailansicht" in normalized:
        score -= 100
    return score


class _StateLawHtmlParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self.norms: list[dict[str, Any]] = []
        self._in_title = False
        self._current: dict[str, Any] | None = None
        self._in_heading = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attr = {key: value for key, value in attrs}
        if tag == "h1":
            self._in_title = True
        if tag in {"section", "article", "div"} and "data-state-law-norm" in attr:
            unit = (attr.get("data-unit") or "").strip().lower()
            value = (attr.get("data-value") or "").strip()
            if unit in {"par", "art"} and value:
                self._current = {"unit": unit, "value": value, "text": "", "title": None}
        if self._current is not None and tag in {"h2", "h3"}:
            self._in_heading = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "h1":
            self._in_title = False
        if self._current is not None and tag in {"h2", "h3"}:
            self._in_heading = False
        if self._current is not None and tag in {"section", "article", "div"}:
            self.norms.append(self._current)
            self._current = None
            self._in_heading = False

    def handle_data(self, data: str) -> None:
        value = data.strip()
        if not value:
            return
        if self._in_title and self.title is None:
            self.title = value
        if self._current is None:
            return
        if self._in_heading and self._current.get("title") is None:
            self._current["title"] = _clean_text(value)
            return
        self._current["text"] = f"{self._current['text']} {value}"


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title: str | None = None
        self._parts: list[str] = []
        self._ignore_depth = 0
        self._in_h1 = False

    @property
    def text(self) -> str:
        raw = " ".join(self._parts)
        raw = re.sub(r" *\n+ *", "\n", raw)
        lines = [_clean_text(line) for line in raw.splitlines()]
        return "\n".join(line for line in lines if line)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in NOISE_TAGS:
            self._ignore_depth += 1
            return
        if self._ignore_depth:
            return
        if tag == "h1":
            self._in_h1 = True
        if tag in BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in NOISE_TAGS and self._ignore_depth:
            self._ignore_depth -= 1
            return
        if self._ignore_depth:
            return
        if tag == "h1":
            self._in_h1 = False
        if tag in BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if self._ignore_depth:
            return
        value = data.strip()
        if not value:
            return
        if self._in_h1 and self.title is None:
            self.title = _clean_text(value)
        self._parts.append(value)
