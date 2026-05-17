---
type: documentation
entity: module
module: "corpus"
version: 1.0
---

# Module: corpus

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `src/legal_text_mcp_de/corpus/` package manages v2 corpus bundle discovery,
loading, caching, and signature verification. It replaces the v1 pattern of
pointing `DATASET_PATH` at a raw directory; in v2, the corpus is a single
signed `.tar.zst` OCI artifact.

### Responsibility

This module is responsible for:

- defining the Pydantic schema for `BundleManifest` and `BundleEntry`;
- resolving a usable bundle path from (1) a local override, (2) the XDG
  user-level cache, or (3) an `oras pull` download from GHCR;
- caching downloaded bundles under `$XDG_CACHE_HOME/legal-text-mcp-de/`;
- verifying bundle signatures with `cosign verify-blob`.

It is not responsible for parsing law/norm content from the bundle; that
responsibility belongs to `legal_texts/dataset.py` and the normalizer pipeline.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `pydantic` | library | Schema validation for `BundleManifest` and `BundleEntry`. |
| `oras` | external binary | OCI artifact pull from GHCR when auto-download is enabled. |
| `cosign` | external binary | Keyless signature verification (`cosign verify-blob`). |
| `zstandard` | library | Decompression of `.tar.zst` bundles (used by callers). |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `src/legal_text_mcp_de/corpus/bundle_schema.py` | file | `BundleManifest` and `BundleEntry` Pydantic models; `BUNDLE_SCHEMA_VERSION = 2`. |
| `src/legal_text_mcp_de/corpus/loader.py` | file | `load_corpus_bundle` — three-tier lookup (local / cache / download). |
| `src/legal_text_mcp_de/corpus/cache.py` | file | `CorpusCache` — XDG-based per-version file cache. |
| `src/legal_text_mcp_de/corpus/verifier.py` | file | `verify_bundle_signature` — shells out to `cosign verify-blob`. |
| `src/legal_text_mcp_de/corpus/__init__.py` | file | Re-exports `load_corpus_bundle` and `BundleLoadError`. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `BUNDLE_SCHEMA_VERSION` | constant | `bundle_schema.py` | Always `2`; bundle readers assert this before parsing. |
| `BundleEntry` | class | `bundle_schema.py` | One law entry: `canonical_id`, `source_kind`, `source_url`, `content_hash`, `size_bytes`, `law_count`, `norm_count`. |
| `BundleManifest` | class | `bundle_schema.py` | Top-level manifest: `bundle_id`, `built_at`, `source_versions`, `entries`, `signature_method`, `provenance_attestation_url`. |
| `LoadedBundle` | dataclass | `loader.py` | Result: `bundle_path`, `source` (`'local'`/`'cache'`/`'download'`), `version`. |
| `load_corpus_bundle` | function | `loader.py` | Main entry point — returns `LoadedBundle` or raises `BundleLoadError`. |
| `BundleLoadError` | exception | `loader.py` | Raised for missing bundles, failed downloads, and signature failures. |
| `CorpusCache` | class | `cache.py` | Manages `$XDG_CACHE_HOME/legal-text-mcp-de/corpus-<version>.tar.zst`. |
| `verify_bundle_signature` | function | `verifier.py` | Runs `cosign verify-blob`; returns `True` / `False` without raising. |

## Data Flow

1. `server.py` calls `load_corpus_bundle` during startup (`_resolve_dataset_path`).
2. If `settings.dataset_path` is set, the file is used directly (source `'local'`).
3. Otherwise `CorpusCache.find_bundle` checks the XDG cache directory.
4. If not cached and `CORPUS_AUTO_DOWNLOAD=true`, `oras pull` fetches the OCI
   artifact from `ghcr.io/klein-business/legal-text-mcp-de/corpus:{version}`.
5. When `CORPUS_CERT_IDENTITY` is configured, `verify_bundle_signature` is called
   with the Fulcio cert sidecar files (`*.sig`, `*.crt`) before the bundle is used.
6. The resolved `bundle_path` is stored in `settings.dataset_path` for
   `LegalTextRuntime` to load.

## Configuration

| Setting | Default | Purpose |
| ------- | ------- | ------- |
| `DATASET_PATH` | `None` | Direct path override; skips cache and download. |
| `CORPUS_AUTO_DOWNLOAD` | `false` | Enable `oras pull` from GHCR. |
| `CORPUS_VERSION` | `"latest"` | OCI tag to pull (e.g. `"2026-05-17"`). |
| `CORPUS_CERT_IDENTITY` | `None` | Required for cosign verification; disables verify when unset. |

## Inventory Notes

- **Coverage**: full; the module ships with unit tests for all three loading
  paths and signature verification failure handling.
- **Notes**: `cosign` and `oras` must be installed by the operator; the module
  documents this in `docs/operations/verify-with-cosign.md`.
- **See also**: [hosted-deployment](hosted-deployment.md) for the production
  bundle-refresh topology; [mcp-resources](../features/mcp-resources.md) for the
  `legal://corpus/manifest` resource that exposes bundle provenance at runtime.
