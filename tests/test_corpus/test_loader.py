# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path
from unittest.mock import patch

import pytest

from legal_text_mcp_de.corpus.loader import (
    BundleLoadError,
    LoadedBundle,
    load_corpus_bundle,
)


def test_loader_uses_local_path_if_provided(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "cache"))
    bundle = tmp_path / "local.tar.zst"
    bundle.write_bytes(b"local-bytes")
    result: LoadedBundle = load_corpus_bundle(local_path=bundle, auto_download=False)
    assert result.bundle_path == bundle
    assert result.source == "local"


def test_loader_uses_cache_when_present(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache_dir = Path(tmp_path) / "legal-text-mcp-de"
    cache_dir.mkdir()
    cached_bundle = cache_dir / "corpus-test.tar.zst"
    cached_bundle.write_bytes(b"cached")
    result = load_corpus_bundle(local_path=None, auto_download=False, version="test")
    assert result.bundle_path == cached_bundle
    assert result.source == "cache"


def test_loader_fails_when_no_local_no_cache_no_auto_download(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    with pytest.raises(BundleLoadError, match="auto-download disabled"):
        load_corpus_bundle(local_path=None, auto_download=False)


def test_loader_fails_when_local_path_missing(tmp_path: Path):
    missing = tmp_path / "does-not-exist.tar.zst"
    with pytest.raises(BundleLoadError, match="local bundle not found"):
        load_corpus_bundle(local_path=missing, auto_download=False)


def test_loader_auto_download_invokes_oras_pull(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))

    fake_bundle = Path(tmp_path) / "legal-text-mcp-de" / "corpus-1.5.0.tar.zst"

    def fake_oras_pull(oci_ref: str, target: Path) -> None:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b"downloaded")

    with patch("legal_text_mcp_de.corpus.loader._oras_pull", side_effect=fake_oras_pull) as op:
        result = load_corpus_bundle(
            local_path=None,
            auto_download=True,
            version="1.5.0",
            verify_signature=False,
        )
    op.assert_called_once()
    assert result.source == "download"
    assert result.bundle_path == fake_bundle


def test_loader_verify_signature_requires_cert_identity(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    with patch("legal_text_mcp_de.corpus.loader._oras_pull", lambda ref, t: t.write_bytes(b"x")):
        with pytest.raises(BundleLoadError, match="cert_identity"):
            load_corpus_bundle(
                local_path=None,
                auto_download=True,
                version="x",
                verify_signature=True,
                cert_identity=None,
            )
