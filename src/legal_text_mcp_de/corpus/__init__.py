# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Corpus bundle loading, verification, and cache management."""

from legal_text_mcp_de.corpus.bundle_schema import (
    BUNDLE_SCHEMA_VERSION,
    BundleEntry,
    BundleManifest,
)
from legal_text_mcp_de.corpus.cache import CorpusCache
from legal_text_mcp_de.corpus.loader import (
    BundleLoadError,
    LoadedBundle,
    load_corpus_bundle,
)
from legal_text_mcp_de.corpus.verifier import verify_bundle_signature

__all__ = [
    "BUNDLE_SCHEMA_VERSION",
    "BundleEntry",
    "BundleLoadError",
    "BundleManifest",
    "CorpusCache",
    "LoadedBundle",
    "load_corpus_bundle",
    "verify_bundle_signature",
]
