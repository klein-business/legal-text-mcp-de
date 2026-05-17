# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path

from legal_text_mcp_de.corpus.cache import CorpusCache


def test_cache_dir_is_created_on_demand(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache = CorpusCache()
    assert cache.path.exists()
    assert cache.path.name == "legal-text-mcp-de"


def test_cache_stores_and_retrieves_bundle(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache = CorpusCache()
    (cache.path / "corpus-2026-05.tar.zst").write_bytes(b"payload")
    found = cache.find_bundle(version="2026-05")
    assert found is not None
    assert found.read_bytes() == b"payload"
    assert cache.find_bundle(version="2099-12") is None


def test_cache_store_bundle_writes_bytes(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    cache = CorpusCache()
    written = cache.store_bundle(version="2026-06", payload=b"newdata")
    assert written.exists()
    assert written.read_bytes() == b"newdata"
