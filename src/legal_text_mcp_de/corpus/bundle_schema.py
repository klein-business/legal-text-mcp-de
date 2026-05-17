# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Schema definitions for the v2 corpus bundle manifest."""

from __future__ import annotations

from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

BUNDLE_SCHEMA_VERSION: Final[Literal[2]] = 2


class BundleEntry(BaseModel):
    """One law within a corpus bundle."""

    model_config = ConfigDict(extra="forbid")

    canonical_id: str = Field(description="Stable identifier, e.g. 'bgb'.")
    source_kind: str = Field(description="'gesetze-im-internet', 'state-bayern', 'eur-lex-cellar', etc.")
    source_url: str = Field(description="Canonical download URL of the raw payload.")
    content_hash: str = Field(description="sha256:<hex> of the raw payload.")
    size_bytes: int = Field(ge=0, description="Size of the raw payload in bytes.")
    law_count: int = Field(ge=0, description="Usually 1; some bundles aggregate.")
    norm_count: int = Field(ge=0, description="Total norm/paragraph count across all laws in this entry.")


class BundleManifest(BaseModel):
    """Top-level manifest of a corpus bundle."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal[2] = Field(
        default=BUNDLE_SCHEMA_VERSION, description="Bundle format schema version (currently 2)."
    )
    bundle_id: str = Field(description="Date-derived id, e.g. '2026-05-17-corpus'.")
    built_at: str = Field(description="ISO 8601 UTC timestamp ending in Z.")
    source_versions: dict[str, str] = Field(description="Tool/source version pinning.")
    entries: list[BundleEntry] = Field(description="One entry per law in the bundle.")
    signature_method: str = Field(description="'cosign-keyless' or 'none' for unsigned dev builds.")
    provenance_attestation_url: str | None = Field(
        default=None, description="Optional URL to the SLSA provenance attestation for this bundle."
    )
