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
from prepare_data.eu_acts import AIAct, DMAAct, DSAAct, EPrivacyAct
from prepare_data.normalizer import normalize_for_runtime
from prepare_data.state_law import (
    BayernStateLaw,
    BWStateLaw,
    HEStateLaw,
    NDSStateLaw,
    NRWStateLaw,
)

# Maps source-spec code → concrete scraper class.
# Typed as Any-value dicts so that mypy does not reject the concrete classes
# for not being exact subtypes of the Protocol / structural stub.
_STATE_REGISTRY: dict[str, Any] = {
    "by": BayernStateLaw,
    "nrw": NRWStateLaw,
    "bw": BWStateLaw,
    "nds": NDSStateLaw,
    "he": HEStateLaw,
}

_EU_REGISTRY: dict[str, Any] = {
    "32002L0058": EPrivacyAct,
    "32022R2065": DSAAct,
    "32022R1925": DMAAct,
    "32024R1689": AIAct,
}


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _collect_bund_laws() -> list[dict[str, Any]]:
    """Stub — lawde end-to-end integration is deferred to a later task."""
    return []


def _collect_state_laws(state_codes: list[str]) -> list[dict[str, Any]]:
    """Run each state-law scraper, normalise its laws into the runtime dict shape."""
    out: list[dict[str, Any]] = []
    retrieved_at = _utc_now_iso()
    for code in state_codes:
        klass = _STATE_REGISTRY.get(code)
        if not klass:
            print(f"WARN: unknown state code {code}, skipping", flush=True)
            continue
        source = klass()
        try:
            index = source.fetch_index()
        except Exception as exc:
            print(f"WARN: {code}: fetch_index failed: {exc}", flush=True)
            continue
        for summary in index:
            try:
                raw = source.fetch_law(summary.law_id)
                norm = source.normalize(raw)
                out += normalize_for_runtime([norm], source_kind=f"state-{code}", retrieved_at=retrieved_at)
            except Exception as exc:
                print(f"WARN: {code}/{summary.law_id} failed: {exc}", flush=True)
                continue
    return out


def _collect_eu_acts(celexes: list[str]) -> list[dict[str, Any]]:
    """Run each EU-act loader, normalise into the runtime dict shape."""
    out: list[dict[str, Any]] = []
    retrieved_at = _utc_now_iso()
    for celex in celexes:
        klass = _EU_REGISTRY.get(celex)
        if not klass:
            print(f"WARN: unknown CELEX {celex}, skipping", flush=True)
            continue
        try:
            loader = klass()
            norm = loader.fetch_and_normalise()
            out += normalize_for_runtime([norm], source_kind="eur-lex-cellar", retrieved_at=retrieved_at)
        except Exception as exc:
            print(f"WARN: CELEX {celex} failed: {exc}", flush=True)
            continue
    return out


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
