# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Corpus bundle loading, verification, and cache management."""

from legal_text_mcp_de.corpus.bundle_schema import (
    BUNDLE_SCHEMA_VERSION,
    BundleEntry,
    BundleManifest,
)

__all__ = ["BUNDLE_SCHEMA_VERSION", "BundleEntry", "BundleManifest"]
