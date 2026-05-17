# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Packs normalised laws into a .tar.zst corpus bundle with manifest.

Layout inside the tarball:
    manifest.json           — BundleManifest JSON
    laws/<canonical_id>.json — one file per law (NormalizedDataset.load format)

The bundle is zstandard-compressed (level 15) for a good size/decode trade-off.
"""

from __future__ import annotations

import io
import json
import tarfile
from pathlib import Path
from typing import Any

import zstandard

from legal_text_mcp_de.corpus.bundle_schema import (
    BUNDLE_SCHEMA_VERSION,
    BundleEntry,
    BundleManifest,
)


def pack_bundle(
    laws: list[dict[str, Any]],
    out_path: Path,
    *,
    bundle_id: str,
    built_at: str,
    source_versions: dict[str, str],
    signature_method: str = "none",
) -> BundleManifest:
    """Write a corpus bundle to ``out_path``. Returns the manifest used."""
    entries: list[BundleEntry] = []
    for law in laws:
        law_bytes = json.dumps(law, ensure_ascii=False).encode("utf-8")
        entries.append(
            BundleEntry(
                canonical_id=law["canonical_id"],
                source_kind=law["source"]["source_kind"],
                source_url=law["source"]["source_url"],
                content_hash=law["source"]["content_hash"],
                size_bytes=len(law_bytes),
                law_count=1,
                norm_count=len(law["norms"]),
            )
        )
    manifest = BundleManifest(
        schema_version=BUNDLE_SCHEMA_VERSION,
        bundle_id=bundle_id,
        built_at=built_at,
        source_versions=source_versions,
        entries=entries,
        signature_method=signature_method,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cctx = zstandard.ZstdCompressor(level=15)
    with open(out_path, "wb") as raw_out:
        with cctx.stream_writer(raw_out) as writer:
            with tarfile.open(fileobj=writer, mode="w|") as tar:
                _add_text_file(tar, "manifest.json", manifest.model_dump_json(indent=2))
                for law in laws:
                    _add_text_file(
                        tar,
                        f"laws/{law['canonical_id']}.json",
                        json.dumps(law, ensure_ascii=False),
                    )
    return manifest


def _add_text_file(tar: tarfile.TarFile, name: str, content: str) -> None:
    data = content.encode("utf-8")
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    tar.addfile(info, io.BytesIO(data))
