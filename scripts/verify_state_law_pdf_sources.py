#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from legal_texts.state_law_coverage import build_state_law_pdf_gate_artifact  # type: ignore[import-not-found]
from legal_texts.state_law_inventory import load_state_law_inventory  # type: ignore[import-not-found]


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify final state-law PDF/source limitation coverage.")
    parser.add_argument("--inventory", required=True, help="state_law_sources.v1.json path.")
    parser.add_argument("--phase9-outcomes", required=True, help="Phase 9 state-law adapter gate JSON path.")
    parser.add_argument("--package-dir", required=True, help="Generated state-law package directory.")
    parser.add_argument(
        "--output", required=True, help="Path where state-law-pdf-source-gate.v1 JSON should be written."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    inventory = load_state_law_inventory(Path(args.inventory))
    phase9_artifact = json.loads(Path(args.phase9_outcomes).read_text(encoding="utf-8"))
    package_dir = Path(args.package_dir)
    output = Path(args.output)
    coverage_path = package_dir / "state-law-coverage.json"
    gate = build_state_law_pdf_gate_artifact(
        inventory,
        phase9_artifact,
        package_dir=package_dir,
        coverage_path=coverage_path,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(gate, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if gate["validation_errors"]:
        for error in gate["validation_errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
