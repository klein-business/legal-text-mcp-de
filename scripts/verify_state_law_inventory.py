#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from legal_texts.state_law_inventory import (  # type: ignore[import-untyped]
    load_state_law_inventory,
    load_state_law_limitations,
    validate_state_law_inventory,
)


Fetch = Callable[[str], tuple[int, dict[str, str], bytes]]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify German state-law inventory reachability.")
    parser.add_argument("--inventory", required=True, help="state_law_sources.v1.json path.")
    parser.add_argument("--limitations", required=True, help="state_law_limitations.v1.json path.")
    parser.add_argument(
        "--write-artifact", required=True, help="Path for state-law-inventory-reachability.v1 artifact."
    )
    parser.add_argument("--fixture-mode", action="store_true", help="Use deterministic fake fetches for tests.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inventory_path = Path(args.inventory)
    limitations_path = Path(args.limitations)
    inventory = load_state_law_inventory(inventory_path)
    limitations = load_state_law_limitations(limitations_path)
    artifact = build_artifact(
        inventory,
        limitations,
        fetch=fixture_fetch if args.fixture_mode else default_fetch,
        checked_at=utc_now(),
        inventory_path=str(inventory_path),
        limitations_path=str(limitations_path),
    )
    output = Path(args.write_artifact)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if artifact["validation_errors"]:
        for error in artifact["validation_errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


def build_artifact(
    inventory: dict[str, Any],
    limitations: list[dict[str, Any]],
    *,
    fetch: Fetch,
    checked_at: str,
    inventory_path: str | None = None,
    limitations_path: str | None = None,
) -> dict[str, Any]:
    validation_errors = validate_state_law_inventory(inventory, limitations)
    limitation_by_id = {limitation["limitation_id"]: limitation for limitation in limitations}
    results = []
    adapter_class_counts: Counter[str] = Counter()
    for record in inventory.get("states", []):
        adapter_class = record.get("adapter_class")
        adapter_class_counts[str(adapter_class)] += 1
        state_result = {
            "state_code": record.get("state_code"),
            "state_name": record.get("state_name"),
            "law_id": record.get("law_id"),
            "adapter_class": adapter_class,
            "source_format": record.get("source_format"),
            "stability_note": record.get("stability_note"),
            "sources": [],
        }
        if adapter_class == "limitation_only":
            limitation = limitation_by_id.get(record.get("source_limitation_id"))
            state_result["terminal_state"] = "source_unavailable"
            state_result["source_limitation_id"] = record.get("source_limitation_id")
            state_result["limitation"] = limitation
            state_result["sources"].append(
                {
                    "url": record.get("official_sources", [{}])[0].get("url")
                    if record.get("official_sources")
                    else None,
                    "status": "limitation_only",
                    "checked_at": checked_at,
                    "content_type": "unknown",
                }
            )
            results.append(state_result)
            continue
        state_result["terminal_state"] = "inventory_checked"
        for source in record.get("official_sources", []):
            state_result["sources"].append(_fetch_source(source, fetch, checked_at))
        validation_errors.extend(_validate_reachability_result(record, state_result))
        results.append(state_result)
    return {
        "schema_version": "state-law-inventory-reachability.v1",
        "checked_at": checked_at,
        "inventory_path": inventory_path,
        "limitations_path": limitations_path,
        "state_count": len(results),
        "adapter_class_counts": dict(sorted(adapter_class_counts.items())),
        "results": results,
        "validation_errors": validation_errors,
    }


def default_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    request = urllib.request.Request(url, headers={"User-Agent": "legal-text-mcp-de/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, {key.lower(): value for key, value in response.headers.items()}, response.read()
    except urllib.error.HTTPError as exc:
        return exc.code, {key.lower(): value for key, value in exc.headers.items()}, exc.read()


def fixture_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    if "unavailable" in url:
        return 503, {"content-type": "text/plain"}, b"unavailable"
    return 200, {"content-type": "text/html; charset=utf-8"}, b"<html>official state law</html>"


def _fetch_source(source: dict[str, Any], fetch: Fetch, checked_at: str) -> dict[str, Any]:
    url = source.get("url")
    result = {
        "url": url,
        "format": source.get("format"),
        "publisher": source.get("publisher"),
        "checked_at": checked_at,
    }
    try:
        status, headers, body = fetch(str(url))
    except Exception as exc:
        result.update(
            {
                "status": 0,
                "error_code": "fetch_exception",
                "error": str(exc),
                "content_type": "",
            }
        )
        return result
    content_type = headers.get("content-type", headers.get("Content-Type", ""))
    result.update(
        {
            "status": status,
            "content_type": content_type,
            "bytes": len(body),
            "content_sha256": hashlib.sha256(body).hexdigest(),
        }
    )
    if status >= 400:
        result["error_code"] = f"http_{status}"
    return result


def _validate_reachability_result(record: dict[str, Any], state_result: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    state_code = record.get("state_code")
    source_format = record.get("source_format")
    for source in state_result.get("sources", []):
        status = source.get("status")
        content_type = str(source.get("content_type") or "").lower()
        url = source.get("url")
        if not isinstance(status, int) or status < 200 or status >= 400:
            errors.append(f"{state_code}: non-limitation source {url} is not reachable with 2xx/3xx status")
            continue
        if source_format == "pdf" and "pdf" not in content_type:
            errors.append(f"{state_code}: source_format pdf does not match content_type {content_type}")
        elif source_format == "xml" and "xml" not in content_type:
            errors.append(f"{state_code}: source_format xml does not match content_type {content_type}")
        elif source_format == "html" and "html" not in content_type:
            errors.append(f"{state_code}: source_format html does not match content_type {content_type}")
    return errors


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
