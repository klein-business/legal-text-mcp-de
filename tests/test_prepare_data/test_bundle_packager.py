# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import tarfile
from pathlib import Path

import zstandard

from legal_text_mcp_de.corpus.bundle_schema import BundleManifest
from prepare_data.bundle_packager import pack_bundle


SAMPLE_LAW = {
    "canonical_id": "bgb",
    "display_code": "BGB",
    "display_name": "BGB",
    "aliases": [],
    "norm_count": 1,
    "stand_date": None,
    "source": {
        "source_kind": "gesetze-im-internet",
        "source_identifier": "bgb",
        "source_url": "https://www.gesetze-im-internet.de/bgb/xml.zip",
        "retrieved_at": "2026-05-17T03:00:00Z",
        "stand_date": None,
        "stand_date_status": "not_exposed",
        "content_hash": "sha256:abc",
    },
    "norms": [{"norm_id": "par:1", "title": "Test", "text": "Body"}],
}


def test_pack_bundle_creates_tar_zst_with_manifest(tmp_path: Path):
    out_path = tmp_path / "corpus.tar.zst"
    manifest = pack_bundle(
        laws=[SAMPLE_LAW],
        out_path=out_path,
        bundle_id="2026-05-17-test",
        built_at="2026-05-17T03:00:00Z",
        source_versions={"test": "1"},
    )
    assert isinstance(manifest, BundleManifest)
    assert out_path.exists()
    # Decompress and inspect
    with open(out_path, "rb") as f:
        dctx = zstandard.ZstdDecompressor()
        with dctx.stream_reader(f) as reader:
            with tarfile.open(fileobj=reader, mode="r|") as tar:
                names = tar.getnames()
    assert "manifest.json" in names
    assert "laws/bgb.json" in names


def test_pack_bundle_manifest_round_trips(tmp_path: Path):
    out_path = tmp_path / "corpus.tar.zst"
    pack_bundle(
        laws=[SAMPLE_LAW],
        out_path=out_path,
        bundle_id="2026-05-17-test",
        built_at="2026-05-17T03:00:00Z",
        source_versions={"test": "1"},
    )
    # Read manifest from inside the bundle
    with open(out_path, "rb") as f:
        dctx = zstandard.ZstdDecompressor()
        with dctx.stream_reader(f) as reader:
            with tarfile.open(fileobj=reader, mode="r|") as tar:
                for member in tar:
                    if member.name == "manifest.json":
                        raw = tar.extractfile(member).read().decode("utf-8")
                        break
                else:
                    raise AssertionError("manifest.json missing")
    parsed = BundleManifest.model_validate_json(raw)
    assert parsed.bundle_id == "2026-05-17-test"
    assert parsed.schema_version == 2
    assert len(parsed.entries) == 1
    assert parsed.entries[0].canonical_id == "bgb"
    assert parsed.entries[0].size_bytes > 0


def test_pack_bundle_creates_parent_dir(tmp_path: Path):
    out_path = tmp_path / "nested" / "deep" / "corpus.tar.zst"
    pack_bundle(
        laws=[SAMPLE_LAW],
        out_path=out_path,
        bundle_id="t",
        built_at="2026-05-17T00:00:00Z",
        source_versions={},
    )
    assert out_path.exists()
