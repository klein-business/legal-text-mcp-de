<p align="center">
  <img src="assets/readme-banner.svg" alt="legal-text-mcp-de: German legal text MCP server banner" width="100%">
</p>

<p align="center">
  <a href="https://github.com/klein-business/legal-text-mcp-de"><img alt="Repository" src="https://img.shields.io/badge/repo-klein--business%2Flegal--text--mcp--de-111827?style=for-the-badge&logo=github"></a>
  <img alt="Python 3.12 / 3.13" src="https://img.shields.io/badge/python-3.12%20%7C%203.13-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img alt="MCP streamable HTTP" src="https://img.shields.io/badge/MCP-streamable%20HTTP-0EA5E9?style=for-the-badge">
  <img alt="FastAPI" src="https://img.shields.io/badge/FastAPI-HTTP%20API-009688?style=for-the-badge&logo=fastapi&logoColor=white">
  <img alt="License: Apache 2.0" src="https://img.shields.io/badge/license-Apache%202.0-16A34A?style=for-the-badge">
</p>

# legal-text-mcp-de

`legal-text-mcp-de` is a Python [Model Context Protocol](https://modelcontextprotocol.io)
server and HTTP API for loading, validating, searching, and resolving
**German legal texts** with source provenance.

It is **local or server-side infrastructure**: no SaaS, no billing, no
accounts, no tenant model, and **no legal advice**. The runtime loads
either the committed fixture packages used by fast CI or a generated
production corpus package built outside Git. Official text comes from
`gesetze-im-internet.de` for German federal laws and from EUR-Lex /
Cellar for EU acts such as the GDPR.

> **No legal advice.** This software returns text and structured
> metadata. It does not interpret the law, advise on it, or produce
> any legal conclusion. The maintainer assumes no liability for use
> in legal decision-making contexts.

Older internal documentation has been archived under
[docs-legacy/summary.md](docs-legacy/summary.md).

## Status

| | |
| --- | --- |
| Lifecycle | Pre-`v1.0.0` public release in preparation |
| Versioning | [SemVer 2.0.0](https://semver.org/spec/v2.0.0.html) (stability contract starts at `v1.0.0`) |
| Licence | Apache License 2.0 — see [LICENSE](LICENSE) and [NOTICE](NOTICE) |
| Upstream | Derived from [floleuerer/deutsche-gesetze-mcp](https://github.com/floleuerer/deutsche-gesetze-mcp) (MIT, preserved) |

## Features

- **MCP tools** for listing laws, fetching norms, resolving citations,
  full-text search, and source provenance.
- **HTTP API** (FastAPI) over the same runtime, with structured
  `/health`, `/ready`, `/laws`, `/search`, and OpenAPI endpoints.
- **Provenance-first design**: every law and norm carries source URL,
  fetch timestamp, content hash, and the parser path it traversed.
- **Two corpus modes**: committed fixture packages for deterministic
  tests and CI, or a generated production package built from official
  sources at runtime.
- **No editorial bundling**: this repository ships tooling, not legal
  text. Texts are loaded from official sources at runtime.

## Quickstart

### Run the MCP server with the committed fixture corpus

```bash
uv sync --all-groups

DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run python mcp/server.py
```

The default transport is streamable HTTP at
`http://localhost:8001/mcp`.

### Run the HTTP API

```bash
DATASET_PATH=mcp/tests/fixtures/normalized \
STRICT_STARTUP=true \
PYTHONPATH=mcp \
uv run uvicorn http_api:app --host 127.0.0.1 --port 8080
```

### Docker

The Docker image does not bundle legal text data. Mount a validated
package at `/data/legal-texts`:

```bash
docker build -t legal-text-mcp-de .
docker run --rm -p 8001:8001 \
  -v /path/to/legal-text-package:/data/legal-texts:ro \
  legal-text-mcp-de
```

## Data Sources

| Source | Coverage | Reuse position |
| --- | --- | --- |
| `gesetze-im-internet.de` | German federal laws | Public-domain-equivalent under §5 (1) UrhG |
| EUR-Lex / Cellar (`publications.europa.eu`) | EU acts (GDPR, AI Act, Data Act, …) | Reuse permitted under Commission Decision 2011/833/EU with attribution |

No text from these sources is committed to this repository. The
generated-corpus pipeline fetches them at build time and stores
provenance in a manifest.

## MCP Tools

See the [MCP tools reference](docs/features/mcp-law-tools.md) for the
full surface. Highlights:

- `list_laws(query?)` — list loaded laws with optional metadata filter.
- `get_law(code)` — law metadata + normalised norm summaries.
- `get_norm(code, norm)` — return one structured norm.
- `search_laws(query, codes?)` — search normalised texts.
- `resolve_citation(...)` — resolve structured citations without legal
  interpretation.
- `get_source_metadata(code?)`, `get_source_limitations(...)`,
  `get_corpus_coverage()`, `get_related_norms(code, norm)`.

MCP tools return JSON-compatible objects. They do not return
double-serialised JSON strings.

## HTTP API

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Liveness |
| `GET` | `/ready` | Readiness |
| `GET` | `/laws` | List laws |
| `GET` | `/laws/{code}` | Law detail |
| `GET` | `/laws/{code}/norms/{norm}` | Norm detail |
| `GET` | `/laws/{code}/norms/{norm}/relationships` | Relationship metadata |
| `GET` | `/corpus/coverage` | Corpus coverage summary |
| `GET` | `/corpus/source-limitations` | Source limitations query |
| `GET` | `/search` | Search |
| `GET` | `/openapi.json` | OpenAPI document |

Article-plus-section paths must be URL-encoded:

```
/laws/egbgb/norms/art%3A246a%2Fpar%3A1
```

## Documentation

- [Project overview](docs/overview.md)
- [MCP tools reference](docs/features/mcp-law-tools.md)
- [Supported laws](docs/features/supported-laws.md)
- [Source provenance](docs/features/source-provenance.md)
- [Scope and invariants](docs/features/known-issues.md)

## Development

```bash
uv sync --all-groups
PYTHONPATH=mcp uv run --group dev pytest mcp/tests -v
```

The full fixture-backed release gate:

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py
```

The public-flip readiness gate:

```bash
PYTHONPATH=mcp uv run --group dev python scripts/verify_pre_flip.py
```

## Contributing

This is a pre-`v1.0.0` repository preparing for public release.
Contribution guidelines, code of conduct, and security policy land in
the next phases of the public-release programme.

## Licence and acknowledgements

This project is licensed under the [Apache License 2.0](LICENSE).
See [NOTICE](NOTICE) for required attribution.

Derived from [floleuerer/deutsche-gesetze-mcp](https://github.com/floleuerer/deutsche-gesetze-mcp)
(Copyright (c) 2025 Florian Leuerer, MIT). Upstream licence terms are
preserved in [licenses/MIT-floleuerer.txt](licenses/MIT-floleuerer.txt).
