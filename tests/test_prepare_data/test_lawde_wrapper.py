# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import hashlib
from pathlib import Path

from prepare_data import FetchResult, LawdeIncremental


def test_incremental_fetch_skips_unchanged_laws(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    # Seed cache with an already-known content hash for 'bgb'
    (cache_dir / "bgb.sha256").write_text("abc123\n", encoding="utf-8")

    def fake_head(law_id: str) -> str:
        return "abc123" if law_id == "bgb" else "fresh"

    def fake_fetch(law_id: str) -> bytes:
        if law_id == "bgb":
            raise AssertionError("Should not refetch unchanged bgb")
        return b"fresh-bytes"

    inc = LawdeIncremental(cache_dir=cache_dir, head_fn=fake_head, fetch_fn=fake_fetch)
    result = inc.update(law_ids=["bgb", "stgb"])
    assert isinstance(result, FetchResult)
    assert result.skipped == ["bgb"]
    assert result.updated == ["stgb"]
    assert result.failed == []


def test_incremental_fetch_records_failures(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    def fake_head(law_id: str) -> str:
        if law_id == "broken_head":
            raise RuntimeError("HEAD 500")
        return "h1"

    def fake_fetch(law_id: str) -> bytes:
        if law_id == "broken_fetch":
            raise RuntimeError("GET 503")
        return b"ok"

    inc = LawdeIncremental(cache_dir=cache_dir, head_fn=fake_head, fetch_fn=fake_fetch)
    result = inc.update(law_ids=["good", "broken_head", "broken_fetch"])

    assert result.updated == ["good"]
    assert {law_id for law_id, _ in result.failed} == {"broken_head", "broken_fetch"}


def test_incremental_persists_new_hash_and_body(tmp_path: Path):
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    inc = LawdeIncremental(
        cache_dir=cache_dir,
        head_fn=lambda law_id: "deadbeef",
        fetch_fn=lambda law_id: b"law-body",
    )
    inc.update(law_ids=["bgb"])
    hash_file = cache_dir / "bgb.sha256"
    body_file = cache_dir / "bgb.bin"
    assert hash_file.exists()
    assert body_file.exists()
    # The recorded hash should be sha256(b"law-body")
    assert hash_file.read_text().strip() == hashlib.sha256(b"law-body").hexdigest()
    assert body_file.read_bytes() == b"law-body"


def test_lawde_incremental_auto_creates_cache_dir(tmp_path: Path):
    nested = tmp_path / "deep" / "cache"
    assert not nested.exists()
    inc = LawdeIncremental(
        cache_dir=nested,
        head_fn=lambda law_id: "h",
        fetch_fn=lambda law_id: b"body",
    )
    assert nested.exists()
    # And it still works end-to-end
    result = inc.update(law_ids=["bgb"])
    assert result.updated == ["bgb"]
