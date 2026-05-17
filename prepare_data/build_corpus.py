# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""CLI entry point: build a corpus bundle from selected sources.

Usage::

    python -m prepare_data.build_corpus \\
        --output corpus.tar.zst \\
        --sources bund,land:by,land:nrw,eu:32016R0679

Source spec syntax:
    bund            — federal laws via lawde
    land:<code>     — state law (by, nrw, bw, nds, he)
    eu:<celex>      — EU act by CELEX number
"""

from __future__ import annotations

import argparse
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from prepare_data.bundle_packager import pack_bundle


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _collect_bund_laws() -> list[dict[str, Any]]:
    """Stub — wired in Task A16 once lawde_wrapper is integrated end-to-end."""
    return []


def _collect_state_laws(state_codes: list[str]) -> list[dict[str, Any]]:
    """Stub — wired in Task A16."""
    return []


def _collect_eu_acts(celexes: list[str]) -> list[dict[str, Any]]:
    """Stub — wired in Task A16."""
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="build_corpus", description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--sources",
        required=True,
        help="comma-separated: bund,land:by,land:nrw,eu:32016R0679,...",
    )
    parser.add_argument("--bundle-id", default=None)
    args = parser.parse_args(argv)

    sources = [s.strip() for s in args.sources.split(",") if s.strip()]
    laws: list[dict[str, Any]] = []
    state_codes: list[str] = []
    eu_celexes: list[str] = []
    do_bund = False
    for s in sources:
        if s == "bund":
            do_bund = True
        elif s.startswith("land:"):
            state_codes.append(s.split(":", 1)[1])
        elif s.startswith("eu:"):
            eu_celexes.append(s.split(":", 1)[1])

    if do_bund:
        laws += _collect_bund_laws()
    if state_codes:
        laws += _collect_state_laws(state_codes)
    if eu_celexes:
        laws += _collect_eu_acts(eu_celexes)

    bundle_id = args.bundle_id or _utc_now_iso().replace(":", "").replace("-", "")
    pack_bundle(
        laws=laws,
        out_path=args.output,
        bundle_id=bundle_id,
        built_at=_utc_now_iso(),
        source_versions={"build_corpus": "0.1.0"},
    )
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
