# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from legal_text_mcp_de.corpus.bundle_schema import BundleManifest, BundleEntry


def test_bundle_manifest_round_trips_through_json():
    manifest = BundleManifest(
        schema_version=2,
        bundle_id="2026-05-17-corpus",
        built_at="2026-05-17T03:00:00Z",
        source_versions={"lawde": "0.4.2", "cellar": "2026-05-15"},
        entries=[
            BundleEntry(
                canonical_id="bgb",
                source_kind="gesetze-im-internet",
                source_url="https://www.gesetze-im-internet.de/bgb/xml.zip",
                content_hash="sha256:abc123",
                bytes=3_145_728,
                law_count=1,
                norm_count=2420,
            ),
        ],
        signature_method="cosign-keyless",
        provenance_attestation_url="https://github.com/.../attestations/...",
    )
    raw = manifest.model_dump_json()
    restored = BundleManifest.model_validate_json(raw)
    assert restored == manifest
