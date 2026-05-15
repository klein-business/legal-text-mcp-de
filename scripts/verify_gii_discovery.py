#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from legal_texts.gii_toc import (  # type: ignore[import-not-found]
    DEFAULT_GII_TOC_URL,
    artifact_has_failures,
    fetch_gii_discovery_artifact,
    write_gii_discovery_artifact,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch the GII TOC and write a discovery artifact.")
    parser.add_argument(
        "--output", required=True, help="Path where the gii-discovery-artifact.v1 JSON should be written."
    )
    parser.add_argument("--toc-url", default=DEFAULT_GII_TOC_URL, help="GII TOC URL to fetch.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    artifact = fetch_gii_discovery_artifact(toc_url=args.toc_url)
    write_gii_discovery_artifact(artifact, Path(args.output))
    if artifact_has_failures(artifact):
        for error in artifact.get("validation_errors", []):
            print(error, file=sys.stderr)
        return 1
    print(f"Wrote GII discovery artifact with {artifact['discovered_gii_items']} items to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
