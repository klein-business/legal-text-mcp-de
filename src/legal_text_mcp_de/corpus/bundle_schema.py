# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Schema definitions for the v2 corpus bundle manifest."""

from __future__ import annotations

from pydantic import BaseModel, Field


class BundleEntry(BaseModel):
    """One law within a corpus bundle."""

    canonical_id: str = Field(description="Stable identifier, e.g. 'bgb'.")
    source_kind: str = Field(description="'gesetze-im-internet', 'state-bayern', 'eur-lex-cellar', etc.")
    source_url: str
    content_hash: str = Field(description="sha256:<hex> of the raw payload.")
    bytes: int = Field(ge=0)
    law_count: int = Field(ge=0, description="Usually 1; some bundles aggregate.")
    norm_count: int = Field(ge=0)


class BundleManifest(BaseModel):
    """Top-level manifest of a corpus bundle."""

    schema_version: int = Field(description="Bundle format schema version (currently 2).")
    bundle_id: str = Field(description="Date-derived id, e.g. '2026-05-17-corpus'.")
    built_at: str = Field(description="ISO 8601 UTC timestamp ending in Z.")
    source_versions: dict[str, str] = Field(description="Tool/source version pinning.")
    entries: list[BundleEntry]
    signature_method: str = Field(description="'cosign-keyless' or 'none' for unsigned dev builds.")
    provenance_attestation_url: str | None = None
