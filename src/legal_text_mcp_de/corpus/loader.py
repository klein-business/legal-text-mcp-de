# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Detect a local corpus bundle, OR fetch the latest from a GHCR OCI artifact."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from legal_text_mcp_de.corpus.cache import CorpusCache
from legal_text_mcp_de.corpus.verifier import verify_bundle_signature


class BundleLoadError(RuntimeError):
    """Raised when a corpus bundle cannot be located or verified."""


@dataclass(frozen=True)
class LoadedBundle:
    """Result of a successful corpus-bundle lookup."""

    bundle_path: Path
    source: str  # 'local' | 'cache' | 'download'
    version: str


def load_corpus_bundle(
    *,
    local_path: Path | None,
    auto_download: bool,
    version: str = "latest",
    oci_ref_template: str = ("ghcr.io/klein-business/legal-text-mcp-de/corpus:{version}"),
    verify_signature: bool = True,
    cert_identity: str | None = None,
) -> LoadedBundle:
    """Return a path to a usable corpus bundle.

    Order:
    1. ``local_path`` (if given and exists)
    2. ``CorpusCache.find_bundle(version=…)``
    3. ``oras pull`` from ``oci_ref_template`` into the cache, then
       optionally ``verify_bundle_signature``.

    Raises :class:`BundleLoadError` for missing/invalid bundles.
    """
    if local_path is not None:
        if not local_path.exists():
            raise BundleLoadError(f"local bundle not found: {local_path}")
        return LoadedBundle(bundle_path=local_path, source="local", version=version)

    cache = CorpusCache()
    cached = cache.find_bundle(version=version)
    if cached is not None:
        return LoadedBundle(bundle_path=cached, source="cache", version=version)

    if not auto_download:
        raise BundleLoadError(
            "no local bundle and auto-download disabled; set DATASET_PATH or CORPUS_AUTO_DOWNLOAD=true"
        )

    if verify_signature and not cert_identity:
        raise BundleLoadError("verify_signature requires cert_identity")

    oci_ref = oci_ref_template.format(version=version)
    target = cache.path / f"corpus-{version}.tar.zst"
    _oras_pull(oci_ref, target)
    if verify_signature:
        assert cert_identity is not None  # narrowed above
        if not verify_bundle_signature(target, cert_identity=cert_identity):
            raise BundleLoadError("cosign signature verification failed")
    return LoadedBundle(bundle_path=target, source="download", version=version)


def _oras_pull(oci_ref: str, target: Path) -> None:
    """Shell out to ``oras pull``. Separate function so tests can patch it."""
    target.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["oras", "pull", oci_ref, "--output", str(target.parent)]
    result = subprocess.run(cmd, capture_output=True, check=False)
    if result.returncode != 0:
        raise BundleLoadError(f"oras pull failed: {result.stderr.decode('utf-8', 'replace')}")
