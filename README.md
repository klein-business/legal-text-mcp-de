<p align="center">
  <img src="assets/readme-banner.svg" alt="legal-text-mcp-de: German legal text MCP server banner" width="100%">
</p>

<p align="center">
  <a href="https://github.com/klein-business/legal-text-mcp-de"><img alt="Repository" src="https://img.shields.io/badge/repo-klein--business%2Flegal--text--mcp--de-111827?style=for-the-badge&logo=github"></a>
  <img alt="Python 3.12" src="https://img.shields.io/badge/python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="MCP streamable HTTP" src="https://img.shields.io/badge/MCP-streamable%20HTTP-0EA5E9?style=for-the-badge">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-HTTP%20API-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="Release gate" src="https://img.shields.io/badge/release%20gate-fixture%20CI%20%2B%20E2E-16A34A?style=for-the-badge">
  <img alt="License" src="https://img.shields.io/badge/license-proprietary%20commercial-B91C1C?style=for-the-badge">
</p>

# legal-text-mcp-de

`legal-text-mcp-de` is a Python MCP server and HTTP API for loading,
validating, searching, and resolving German legal texts with source provenance.
It is local/server-side infrastructure: no SaaS, no billing, no accounts, no
tenant model, and no legal advice.

The runtime can load either the committed fixture packages used by fast CI or a
generated production corpus package built outside Git. Official text comes from
`gesetze-im-internet.de` for German federal laws and from EUR-Lex/Cellar for
EU acts such as DSGVO. Third-party privacy-scope inputs are represented only as
relationship metadata and source limitations; editorial text is not copied.

Older repository documentation was archived under [docs-legacy/summary.md](docs-legacy/summary.md).

## Data Modes

| Mode | Location | Purpose |
| ---- | -------- | ------- |
| Fixture packages | `mcp/tests/fixtures/` | Fast deterministic tests, parser samples, HTTP/MCP E2E, and reduced generated-package behavior. |
| Generated corpus artifacts | `.artifacts/`, `data/normalized/`, `data/full-corpus/` | Explicit local or scheduled full-corpus evidence; ignored by Git. |
| Mounted production package | Any validated generated package path | Runtime input for MCP/HTTP through `DATASET_PATH`. |

Generated packages use `package.json`, `manifest.json`, `source-limitations.json`,
`relationships.json`, `readiness.json`, and `search-index.json` alongside
`laws.json` and `norms.json`. The corpus manifest assigns every discovered
source a terminal state: `imported`, `unsupported_format`,
`source_unavailable`, `parse_failed`, or `excluded_by_policy`.

## Corpus Scope

The committed fixture dataset covers the legal-audit law set documented in
[supported laws](docs/features/supported-laws.md). Full-corpus generation is
artifact-backed and expands that contract to:

- all discoverable official GII TOC entries with terminal-state coverage;
- BDSG and TDDDG as critical GII laws with import and runtime resolution
  evidence, or release-blocking upstream `source_unavailable` limitations;
- DSGVO articles 1-99 and recitals from official EUR-Lex/Cellar provenance;
- AI Act, Data Act, and other approved EU neighbor seeds as imported or limited
  official records;
- all 16 German state privacy-law outcomes as imported records or source
  limitations;
- privacy-scope relationship metadata that resolves to official records or
  source limitations.

## MCP Tools

| Tool | Purpose |
| ---- | ------- |
| `list_laws(query?: string)` | List loaded laws, optionally filtered by metadata. |
| `get_law(code: string)` | Return law metadata and normalized norm summaries. |
| `get_norm(code: string, norm: string)` | Return one structured norm by canonical path or shorthand. |
| `resolve_citation(...)` | Resolve exact structured citations without legal interpretation. |
| `search_laws(query: string, codes?: string[])` | Search normalized texts with optional law filters. |
| `get_source_metadata(code?: string)` | Return provenance metadata for one law or all laws. |
| `get_corpus_coverage()` | Return generated-package, manifest, terminal-state, limitation, relationship, and state-law coverage summaries. |
| `get_source_limitations(...)` | Query source limitations by family, terminal state, state code, or law ID. |
| `get_related_norms(code: string, norm: string)` | Return relationship metadata for a resolved norm. |

MCP tools return JSON-compatible objects directly. They do not return
double-serialized JSON strings.

## HTTP API

The HTTP API is a small FastAPI transport over the same runtime:

- `GET /health`
- `GET /ready`
- `GET /laws`
- `GET /laws/{code}`
- `GET /laws/{code}/norms/{norm}`
- `GET /laws/{code}/norms/{norm}/relationships`
- `GET /corpus/coverage`
- `GET /corpus/source-limitations`
- `GET /search`
- `GET /openapi.json`

Article-plus-section norm paths must be URL encoded, for example:

```text
/laws/egbgb/norms/art%3A246a%2Fpar%3A1
```

## Installation

```bash
uv sync --all-groups
```

## Run MCP

Use a validated normalized or generated package:

```bash
DATASET_PATH=/path/to/legal-text-package \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run python mcp/server.py
```

For local development, use the committed fixture dataset:

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run python mcp/server.py
```

The default MCP transport is streamable HTTP on `http://localhost:8001/mcp`.

## Run HTTP API

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run uvicorn http_api:app --host 127.0.0.1 --port 8080
```

## Docker

The Docker image does not clone or generate legal text data. Mount a validated
package at `/data/legal-texts`:

```bash
docker build -t legal-text-mcp-de .
docker run --rm -p 8001:8001 -v /path/to/legal-text-package:/data/legal-texts:ro legal-text-mcp-de
```

## Operational Gates

Fast release verification is fixture-backed and does not download the full
internet corpus. Full-corpus evidence is explicit or scheduled.

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_gii_discovery.py --output .artifacts/gii-discovery/latest.json
```

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_gii_corpus_gate.py --discovery .artifacts/gii-discovery/latest.json --payload-dir <payload-dir> --package-dir .artifacts/gii-corpus/package --output .artifacts/gii-corpus/gate.json
```

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_dsgvo_full_counts.py --package .artifacts/dsgvo/package --policy .artifacts/dsgvo/policy-fixture.json --output .artifacts/dsgvo/full-counts.json
```

```bash
PYTHONPATH=mcp uv run --group dev python scripts/benchmark_corpus_runtime.py --package-dir mcp/tests/fixtures/generated_package --output .artifacts/benchmarks/generated-package-benchmark.json
```

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_full_corpus_bundle.py --gii-artifact .artifacts/gii-corpus/gate.json --dsgvo-artifact .artifacts/dsgvo/full-counts.json --eu-neighbors-artifact .artifacts/eu-neighbors/evidence.json --state-law-artifact .artifacts/state-law/pdf-gate.json --relationships-artifact mcp/legal_texts/data/privacy_scope_seed.v1.json --benchmark-artifact .artifacts/benchmarks/generated-package-benchmark.json --output .artifacts/full-corpus/validation-bundle.json
```

## Tests

Run the full fixture-backed release gate:

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py
```

The release gate covers docs link/image validation, stale workflow checks,
fixture coverage, generated-package validation, operational gate tests, citation
resolution, search, MCP tools, HTTP/OpenAPI, structured errors, source matrix
fixtures, and local HTTP/MCP E2E. The E2E gate starts real localhost HTTP and
MCP streamable-HTTP processes against both the legacy fixture dataset and the
generated-package fixture. It verifies every MCP tool, all documented HTTP
paths through OpenAPI, generated-package recitals/search, source metadata,
coverage, source limitations, relationships, and representative error paths.
Live source probes remain opt-in through `RUN_LIVE_SOURCE_MATRIX=true`.

Run only local network E2E:

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_e2e.py
```

## License

This project is proprietary commercial software. See [LICENSE](LICENSE).

## Documentation

- [Project overview](docs/overview.md)
- [MCP/server module](docs/modules/mcp-server.md)
- [Container runtime](docs/modules/container-runtime.md)
- [Supported laws](docs/features/supported-laws.md)
- [Law loading and indexing](docs/features/law-loading-and-indexing.md)
- [Source provenance](docs/features/source-provenance.md)
- [MCP tools](docs/features/mcp-law-tools.md)
- [HTTP API](docs/features/http-api.md)
- [Scope and invariants](docs/features/known-issues.md)
