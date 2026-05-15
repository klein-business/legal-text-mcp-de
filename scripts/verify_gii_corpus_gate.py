#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from legal_texts.gii_bulk import build_gii_corpus_gate_artifact, write_gii_corpus_gate_artifact


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the fixture/local GII corpus gate.")
    parser.add_argument("--discovery", required=True, help="Path to a gii-discovery-artifact.v1 JSON file.")
    parser.add_argument("--payload-dir", required=True, help="Directory containing local fixture/source payloads.")
    parser.add_argument("--package-dir", required=True, help="Output directory for the generated fixture package.")
    parser.add_argument("--output", required=True, help="Path where the gii-corpus-gate.v1 JSON should be written.")
    parser.add_argument("--retrieved-at", default="2026-05-15T00:00:00Z", help="Timestamp to stamp fixture artifacts with.")
    parser.add_argument("--parser-variant-matrix", help="Optional parser variant matrix JSON path.")
    parser.add_argument("--upstream-limitations", help="Optional upstream source limitation JSON path.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    discovery = json.loads(Path(args.discovery).read_text(encoding="utf-8"))
    upstream_limitations = (
        json.loads(Path(args.upstream_limitations).read_text(encoding="utf-8"))
        if args.upstream_limitations
        else None
    )
    gate = build_gii_corpus_gate_artifact(
        discovery,
        payload_dir=Path(args.payload_dir),
        package_dir=Path(args.package_dir),
        retrieved_at=args.retrieved_at,
        parser_variant_matrix_path=Path(args.parser_variant_matrix) if args.parser_variant_matrix else None,
        upstream_limitations=upstream_limitations,
    )
    write_gii_corpus_gate_artifact(gate, Path(args.output))
    if gate.get("validation_errors"):
        for error in gate["validation_errors"]:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
