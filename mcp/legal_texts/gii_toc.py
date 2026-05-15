from __future__ import annotations

import hashlib
import json
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable

from .manifest import validate_corpus_manifest
from .sources import SOURCE_SPECS


DEFAULT_GII_TOC_URL = "https://www.gesetze-im-internet.de/gii-toc.xml"
GII_DISCOVERY_ARTIFACT_SCHEMA_VERSION = "gii-discovery-artifact.v1"
GII_TOC_PARSER_VERSION = "gii-toc-discovery.v1"
GII_BASE_URL = "https://www.gesetze-im-internet.de"


@dataclass(frozen=True)
class FetchResult:
    status: int
    content: bytes
    url: str


@dataclass(frozen=True)
class GiiTocParseResult:
    items: list[dict[str, Any]]
    malformed_items: list[dict[str, Any]]
    validation_errors: list[str]
    duplicate_count: int = 0


Fetcher = Callable[[str], FetchResult]


def parse_gii_toc(content: bytes | str, *, toc_url: str = DEFAULT_GII_TOC_URL) -> GiiTocParseResult:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    try:
        root = ET.fromstring(raw)
    except ET.ParseError as exc:
        return GiiTocParseResult(
            items=[],
            malformed_items=[],
            validation_errors=[f"TOC XML parse failed: {exc}"],
        )

    toc_sha256 = _sha256(raw)
    items: list[dict[str, Any]] = []
    malformed_items: list[dict[str, Any]] = []
    validation_errors: list[str] = []
    seen: dict[str, int] = {}
    duplicate_count = 0

    for index, element in enumerate(root.iter()):
        if _local_name(element.tag) != "item":
            continue
        raw_xml_zip_link = _find_xml_zip_link(element)
        title = _item_title(element)
        if not raw_xml_zip_link:
            malformed_items.append({
                "index": index,
                "reason": "missing xml.zip link",
                "title": title,
            })
            continue
        xml_zip_link = urllib.parse.urljoin(toc_url, raw_xml_zip_link)
        source_path = _source_path_from_xml_zip_url(xml_zip_link)
        if not source_path:
            malformed_items.append({
                "index": index,
                "reason": "invalid xml.zip source path",
                "link": raw_xml_zip_link,
                "title": title,
            })
            continue
        if source_path in seen:
            validation_errors.append(f"duplicate GII source_path {source_path}")
            duplicate_count += 1
        seen[source_path] = seen.get(source_path, 0) + 1
        items.append(_discovered_source_record(source_path, raw_xml_zip_link, toc_url, toc_sha256, title))

    items.sort(key=lambda item: item["source_path"])
    malformed_items.sort(key=lambda item: item["index"])
    return GiiTocParseResult(
        items=items,
        malformed_items=malformed_items,
        validation_errors=validation_errors,
        duplicate_count=duplicate_count,
    )


def build_gii_discovery_artifact(
    content: bytes | str,
    *,
    toc_url: str = DEFAULT_GII_TOC_URL,
    retrieved_at: str | None = None,
    parser_version: str = GII_TOC_PARSER_VERSION,
    discovery_artifact_id: str | None = None,
) -> dict[str, Any]:
    raw = content.encode("utf-8") if isinstance(content, str) else content
    retrieved_at = retrieved_at or _utc_now()
    parse_result = parse_gii_toc(raw, toc_url=toc_url)
    toc_sha256 = _sha256(raw)
    manifest = _build_manifest(
        parse_result.items,
        retrieved_at=retrieved_at,
        parser_version=parser_version,
        discovery_artifact_id=discovery_artifact_id,
    )
    validation_errors = list(parse_result.validation_errors)
    validation_errors.extend(
        f"malformed GII TOC item at index {item['index']}: {item['reason']}"
        for item in parse_result.malformed_items
    )
    if parse_result.validation_errors and not parse_result.items:
        diagnostic = "; ".join(parse_result.validation_errors)
        toc_limitation = _toc_limitation(
            toc_url,
            retrieved_at,
            "parse_failed",
            f"XML parse failed: {diagnostic}",
            parser_version=parser_version,
            diagnostic=diagnostic,
        )
    else:
        toc_limitation = None
    validation_errors.extend(validate_corpus_manifest(manifest, require_terminal_states=False))
    return _artifact(
        toc_url=toc_url,
        retrieved_at=retrieved_at,
        toc_sha256=toc_sha256,
        parser_version=parser_version,
        discovered_gii_records=parse_result.items,
        manifest=manifest,
        source_paths=sorted({item["source_path"] for item in parse_result.items}),
        duplicate_count=parse_result.duplicate_count,
        malformed_items=parse_result.malformed_items,
        toc_limitation=toc_limitation,
        validation_errors=validation_errors,
    )


def fetch_gii_discovery_artifact(
    *,
    toc_url: str = DEFAULT_GII_TOC_URL,
    fetcher: Fetcher | None = None,
    retrieved_at: str | None = None,
    parser_version: str = GII_TOC_PARSER_VERSION,
) -> dict[str, Any]:
    retrieved_at = retrieved_at or _utc_now()
    fetcher = fetcher or _fetch_url
    try:
        result = fetcher(toc_url)
    except Exception as exc:  # pragma: no cover - exact exception classes vary by transport
        message = f"GII TOC fetch raised {exc.__class__.__name__}: {exc}"
        return _empty_failure_artifact(
            toc_url=toc_url,
            retrieved_at=retrieved_at,
            parser_version=parser_version,
            toc_limitation=_toc_limitation(
                toc_url,
                retrieved_at,
                "source_unavailable",
                message,
                error_code=exc.__class__.__name__,
                details={"toc_url": toc_url, "exception": str(exc)},
            ),
            validation_errors=[message],
        )
    if result.status != 200:
        message = f"GII TOC fetch failed with HTTP status {result.status}"
        return _empty_failure_artifact(
            toc_url=toc_url,
            retrieved_at=retrieved_at,
            parser_version=parser_version,
            toc_limitation=_toc_limitation(
                toc_url,
                retrieved_at,
                "source_unavailable",
                message,
                http_status=result.status,
                details={"toc_url": toc_url, "http_status": result.status},
            ),
            validation_errors=[message],
        )
    return build_gii_discovery_artifact(
        result.content,
        toc_url=result.url or toc_url,
        retrieved_at=retrieved_at,
        parser_version=parser_version,
    )


def write_gii_discovery_artifact(artifact: dict[str, Any], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def artifact_has_failures(artifact: dict[str, Any]) -> bool:
    return bool(artifact.get("toc_limitation") or artifact.get("validation_errors"))


def _fetch_url(url: str) -> FetchResult:
    request = urllib.request.Request(url, headers={"User-Agent": "legal-text-mcp-de/0.1 gii-discovery"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            status = getattr(response, "status", response.getcode())
            return FetchResult(status=status, content=response.read(), url=response.geturl())
    except urllib.error.HTTPError as exc:
        return FetchResult(status=exc.code, content=exc.read(), url=url)


def _discovered_source_record(
    source_path: str,
    original_link: str,
    toc_url: str,
    toc_sha256: str,
    title: str | None,
) -> dict[str, Any]:
    index_url = f"{GII_BASE_URL}/{source_path}/index.html"
    xml_zip_url = f"{GII_BASE_URL}/{source_path}/xml.zip"
    return {
        "source_family": "gii",
        "source_id": f"gii:{source_path}",
        "source_path": source_path,
        "index_url": index_url,
        "xml_zip_url": xml_zip_url,
        "toc_url": toc_url,
        "toc_sha256": toc_sha256,
        "alias_candidates": _alias_candidates(source_path),
        "source_metadata": {
            "source_path": source_path,
            "index_url": index_url,
            "xml_zip_url": xml_zip_url,
            "toc_url": toc_url,
            "original_link": original_link,
            "original_title": title,
        },
    }


def _build_manifest(
    discovered_sources: list[dict[str, Any]],
    *,
    retrieved_at: str,
    parser_version: str,
    discovery_artifact_id: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": "corpus-manifest.v1",
        "dataset_id": "gii-discovery",
        "package_id": f"gii-discovery-{retrieved_at}",
        "created_at": retrieved_at,
        "validation_mode": "discovery",
        "generator": {
            "name": "gii-toc-discovery",
            "version": parser_version,
        },
        "parser_versions": {
            "gii_toc": parser_version,
        },
        "discovered_sources": [
            _manifest_discovered_source(item, discovery_artifact_id)
            for item in discovered_sources
        ],
        "canonical_ids": [],
        "relationship_sources": [],
    }


def _manifest_discovered_source(item: dict[str, Any], discovery_artifact_id: str | None) -> dict[str, Any]:
    return dict(item)


def _artifact(
    *,
    toc_url: str,
    retrieved_at: str,
    toc_sha256: str | None,
    parser_version: str,
    discovered_gii_records: list[dict[str, Any]],
    manifest: dict[str, Any],
    source_paths: list[str],
    duplicate_count: int,
    malformed_items: list[dict[str, Any]],
    toc_limitation: dict[str, Any] | None,
    validation_errors: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": GII_DISCOVERY_ARTIFACT_SCHEMA_VERSION,
        "toc_url": toc_url,
        "retrieved_at": retrieved_at,
        "toc_sha256": toc_sha256,
        "parser_version": parser_version,
        "discovered_gii_items": len(discovered_gii_records),
        "discovered_gii_records": discovered_gii_records,
        "manifest": manifest,
        "source_paths": source_paths,
        "source_path_count": len(source_paths),
        "duplicate_count": duplicate_count,
        "malformed_items": malformed_items,
        "toc_limitation": toc_limitation,
        "validation_errors": validation_errors,
    }


def _empty_failure_artifact(
    *,
    toc_url: str,
    retrieved_at: str,
    parser_version: str,
    toc_limitation: dict[str, Any],
    validation_errors: list[str],
) -> dict[str, Any]:
    manifest = _build_manifest([], retrieved_at=retrieved_at, parser_version=parser_version, discovery_artifact_id=None)
    return _artifact(
        toc_url=toc_url,
        retrieved_at=retrieved_at,
        toc_sha256=None,
        parser_version=parser_version,
        discovered_gii_records=[],
        manifest=manifest,
        source_paths=[],
        duplicate_count=0,
        malformed_items=[],
        toc_limitation=toc_limitation,
        validation_errors=validation_errors,
    )


def _toc_limitation(
    toc_url: str,
    retrieved_at: str,
    terminal_state: str,
    reason: str,
    *,
    parser_version: str | None = None,
    http_status: int | None = None,
    error_code: str | None = None,
    diagnostic: str | None = None,
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    limitation_id_state = terminal_state.replace("_", "-")
    limitation = {
        "limitation_id": f"gii-toc-{limitation_id_state}",
        "source_family": "gii",
        "source_id": "gii:toc",
        "source_path": "toc",
        "index_url": toc_url,
        "xml_zip_url": toc_url,
        "toc_url": toc_url,
        "discovery_artifact_id": "gii-toc-discovery",
        "terminal_state": terminal_state,
        "source_url": toc_url,
        "retrieved_at": retrieved_at,
        "reason": reason,
        "details": details or {"toc_url": toc_url},
    }
    if terminal_state == "source_unavailable":
        limitation["retryable"] = True
    if terminal_state == "parse_failed":
        limitation["diagnostic"] = diagnostic or reason
    if parser_version:
        limitation["parser_version"] = parser_version
    if http_status is not None:
        limitation["http_status"] = http_status
    if error_code is not None:
        limitation["error_code"] = error_code
    return limitation


def _find_xml_zip_link(element: ET.Element) -> str | None:
    candidates: list[str] = []
    for value in element.attrib.values():
        if isinstance(value, str):
            candidates.append(value)
    for child in element.iter():
        if child is element:
            continue
        for value in child.attrib.values():
            if isinstance(value, str):
                candidates.append(value)
        if child.text and "xml.zip" in child.text:
            candidates.append(child.text.strip())
    for candidate in candidates:
        if _source_path_from_xml_zip_url(urllib.parse.urljoin(GII_BASE_URL + "/", candidate)):
            return candidate
    return None


def _source_path_from_xml_zip_url(url: str) -> str | None:
    parsed = urllib.parse.urlparse(url)
    path = parsed.path.rstrip("/")
    if not path.lower().endswith("/xml.zip"):
        return None
    parent = path[: -len("/xml.zip")].rstrip("/")
    source_path = parent.rsplit("/", 1)[-1]
    source_path = urllib.parse.unquote(source_path).strip().lower()
    if not source_path or "/" in source_path or "\\" in source_path:
        return None
    return source_path


def _item_title(element: ET.Element) -> str | None:
    for child in element.iter():
        if _local_name(child.tag) in {"title", "heading", "name"} and child.text and child.text.strip():
            return " ".join(child.text.split())
    text = " ".join(" ".join(element.itertext()).split())
    return text or None


def _alias_candidates(source_path: str) -> list[str]:
    aliases: set[str] = {source_path}
    for spec in SOURCE_SPECS.values():
        if spec.source_kind != "gesetze-im-internet":
            continue
        spec_path = (spec.metadata or {}).get("source_path")
        if spec_path == source_path:
            aliases.add(spec.canonical_id)
            aliases.add(spec.display_code)
            aliases.add(spec.source_identifier)
    return sorted(aliases, key=str.casefold)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
