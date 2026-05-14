---
type: documentation
entity: module
module: "mcp-server"
version: 1.3
---

# Module: mcp-server

> Part of [legal-text-mcp-de](../overview.md)

## Overview

The `mcp/` tree contains the MCP server, HTTP app factory, legal text services, source import helpers, normalization parsers, validated fixture data, and tests.

### Responsibility

This module is responsible for:

- loading a validated normalized dataset package;
- resolving law aliases through a versioned registry;
- returning source-backed law, norm, citation, search, and metadata JSON objects;
- exposing the same domain services through MCP and HTTP;
- failing with structured errors when data or citations are invalid.

It is not responsible for legal evaluation, user management, billing, tenant isolation, or production hosting.

### Dependencies

| Dependency | Type | Purpose |
| ---------- | ---- | ------- |
| `mcp.server.fastmcp.FastMCP` | library | MCP streamable HTTP tool transport. |
| `fastapi`, `uvicorn` | library | HTTP API and OpenAPI generation. |
| `pydantic-settings` | library | Runtime settings from environment and `.env`. |
| `xml.etree.ElementTree`, `zipfile`, `hashlib` | standard library | Source parsing, snapshot handling, and hash manifests. |
| `pytest` | test library | Unit, parser, service, transport, and release-gate tests. |

## Structure

| Path | Type | Purpose |
| ---- | ---- | ------- |
| `mcp/server.py` | file | FastMCP app factory and stable MCP tools. |
| `mcp/http_api.py` | file | FastAPI app factory and HTTP routes. |
| `mcp/http_models.py` | file | Pydantic response models for HTTP/OpenAPI. |
| `mcp/config.py` | file | Runtime settings including dataset path, startup strictness, host, port, and debug flag. |
| `mcp/legal_texts/data/laws.v1.json` | file | Versioned law registry with aliases, canonical IDs, display codes, and source metadata. |
| `mcp/legal_texts/sources.py` | file | Canonical GII and Cellar source specifications plus invalid-path regressions. |
| `mcp/legal_texts/importer.py` | file | Source probing, snapshot download, SHA-256 hashing, manifest generation, and manifest diffing. |
| `mcp/legal_texts/gii_xml.py` | file | GII XML ZIP parser for German legal texts. |
| `mcp/legal_texts/eurlex_xml.py` | file | DSGVO Cellar/Formex article parser. |
| `mcp/legal_texts/normalizer.py` | file | Snapshot-manifest to normalized dataset conversion. |
| `mcp/legal_texts/validation.py` | file | Normalized dataset validation and readiness state generation. |
| `mcp/legal_texts/dataset.py` | file | Normalized dataset loader and lookup layer. |
| `mcp/legal_texts/resolver.py` | file | Structured citation and norm resolver. |
| `mcp/legal_texts/search.py` | file | Deterministic plain-text search over normalized norms. |
| `mcp/legal_texts/runtime.py` | file | Runtime composition for registry, dataset, resolver, search, and metadata services. |
| `mcp/legal_texts/errors.py` | file | Shared structured error codes and envelopes. |
| `mcp/parser.py` | file | Legacy Markdown parser retained for compatibility tests. |
| `mcp/tests/` | dir | Fixture-backed test suite and release-gate coverage. |
| `scripts/verify_release.py` | file | Runs the full release gate and then local network E2E. |
| `scripts/verify_e2e.py` | file | Starts real local HTTP/MCP server processes and verifies both transports end-to-end. |

## Key Symbols

| Symbol | Kind | Location | Purpose |
| ------ | ---- | -------- | ------- |
| `Settings` | class | `mcp/config.py` | Defines `DATASET_PATH`, `STRICT_STARTUP`, host, port, debug, and legacy parser settings. |
| `create_mcp_app` | function | `mcp/server.py` | Builds the FastMCP app and registers the stable tool surface. |
| `create_http_app` | function | `mcp/http_api.py` | Builds the FastAPI app over an injected or configured runtime. |
| `LegalTextRuntime` | class | `mcp/legal_texts/runtime.py` | Shared application service used by both transports. |
| `LawRegistry` | class | `mcp/legal_texts/registry.py` | Resolves aliases to canonical IDs and validates collisions. |
| `NormalizedDataset` | class | `mcp/legal_texts/dataset.py` | Loads `laws.json`, `norms.json`, and readiness data. |
| `resolve_citation` | function | `mcp/legal_texts/resolver.py` | Resolves exact structured legal citations. |
| `SearchService` | class | `mcp/legal_texts/search.py` | Runs deterministic search and produces HTML-free snippets. |
| `validate_dataset_package` | function | `mcp/legal_texts/validation.py` | Verifies normalized dataset readiness. |
| `import_snapshot` | function | `mcp/legal_texts/importer.py` | Downloads source snapshots and writes a hash manifest. |
| `normalize_snapshot` | function | `mcp/legal_texts/normalizer.py` | Produces normalized `laws.json` and `norms.json` from a snapshot manifest. |

## Data Flow

1. Source specs identify official GII XML ZIP URLs and the DSGVO Cellar XML URL.
2. Import helpers download raw artifacts, compute hashes, and write manifests.
3. Normalizers parse raw XML into structured law and norm records.
4. Validation checks required fields, duplicate IDs, source metadata, and readiness.
5. Runtime loads the normalized dataset and exposes registry, citation, search, and metadata services.
6. MCP and HTTP transports delegate to runtime methods and wrap `LegalTextError` as structured JSON.

## Configuration

| Setting | Default | Purpose |
| ------- | ------- | ------- |
| `DATASET_PATH` / `dataset_path` | `None` | Path to a validated normalized dataset package. |
| `STRICT_STARTUP` / `strict_startup` | `true` | Fail process startup when the dataset is missing or invalid. |
| `HOST` / `host` | `0.0.0.0` | MCP bind host. |
| `PORT` / `port` | `8001` | MCP bind port. |
| `DEBUG` / `debug` | `false` | FastMCP debug flag. |

## Test Coverage

The release gate is `PYTHONPATH=mcp python scripts/verify_release.py` from an activated Python 3.12 environment. It runs fixture coverage, source matrix live probes, importer tests, parser/normalizer tests, resolver tests, search tests, MCP tool tests, HTTP/OpenAPI tests, structured error tests, scope checks, and local network E2E through `scripts/verify_e2e.py`.

The E2E script starts temporary Uvicorn/FastMCP processes on free localhost ports, checks HTTP with real network requests, and checks MCP through `mcp.client.streamable_http.streamablehttp_client` plus `ClientSession`. It intentionally waits for MCP TCP readiness rather than probing `/mcp` with a plain HTTP request because MCP streamable HTTP requires protocol-specific headers.

## Inventory Notes

- **Coverage**: full for the supported runtime and tests.
- **Notes**: The legacy Markdown parser remains documented as compatibility code, not as the production data source.
