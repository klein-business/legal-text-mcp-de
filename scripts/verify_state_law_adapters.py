#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path

from legal_texts.state_law import (  # type: ignore[import-untyped]
    build_state_law_adapter_gate_artifact,
    write_state_law_adapter_gate_artifact,
)
from legal_texts.state_law_inventory import load_state_law_inventory, load_state_law_limitations  # type: ignore[import-untyped]


FIXTURE_HTML = """<!doctype html><html lang="de"><body><main data-state-law><h1>Landesdatenschutzgesetz</h1><section data-state-law-norm data-unit="par" data-value="1"><h2>§ 1 Zweck</h2><p>(1) Fixture text.</p></section></main></body></html>""".encode(
    "utf-8"
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the German state-law adapter gate.")
    parser.add_argument("--inventory", required=True, help="state_law_sources.v1.json path.")
    parser.add_argument("--limitations", required=True, help="state_law_limitations.v1.json path.")
    parser.add_argument("--package-dir", required=True, help="Output directory for the generated state-law package.")
    parser.add_argument("--output", required=True, help="Path where state-law-adapter-gate.v1 JSON should be written.")
    parser.add_argument("--retrieved-at", default=None, help="Timestamp to stamp adapter artifacts with.")
    parser.add_argument(
        "--fixture-mode", action="store_true", help="Use deterministic fixture HTML instead of live fetches."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inventory = load_state_law_inventory(Path(args.inventory))
    limitations = load_state_law_limitations(Path(args.limitations))
    artifact = build_state_law_adapter_gate_artifact(
        inventory,
        limitations,
        package_dir=Path(args.package_dir),
        retrieved_at=args.retrieved_at or utc_now(),
        fetch=fixture_fetch if args.fixture_mode else None,
    )
    write_state_law_adapter_gate_artifact(artifact, Path(args.output))
    if artifact["validation_errors"]:
        for error in artifact["validation_errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


def fixture_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
    return 200, {"content-type": "text/html; charset=utf-8"}, FIXTURE_HTML


def utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


if __name__ == "__main__":
    raise SystemExit(main())
