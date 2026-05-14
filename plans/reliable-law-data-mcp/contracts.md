---
type: planning
entity: contracts
plan: "reliable-law-data-mcp"
created: "2026-05-14"
updated: "2026-05-14"
---

# Shared Contracts: reliable-law-data-mcp

> Supports [reliable-law-data-mcp](plan.md)

This document pins down cross-phase contract decisions that must not drift between import, normalization, resolver, search, MCP, and HTTP work.

## Dataset Layout

Phase 1 uses repository-visible fixture data for tests and ignored local data for full imports.

| Path | Tracked? | Purpose |
|------|----------|---------|
| `data/sources/raw/{snapshot_id}/` | no by default | Full raw downloaded source snapshots for local imports. |
| `data/sources/raw/{snapshot_id}/manifest.json` | no by default | Full import manifest for local snapshots. |
| `data/normalized/{dataset_id}/` | no by default | Full normalized dataset package for local serving. |
| `mcp/tests/fixtures/raw/` | yes | Minimal raw fixture extracts for tests. |
| `mcp/tests/fixtures/normalized/` | yes | Minimal normalized JSON fixture records for tests. |
| `mcp/tests/golden/` | yes | Golden resolver/search/MCP/HTTP JSON outputs. |
| `plans/reliable-law-data-mcp/source-matrix.md` | yes | Human-reviewed source truth table. |

## Field Classification

Field classifications are normative for import and validation.

| Class | Meaning | Handling |
|-------|---------|----------|
| required | Must be present and valid for serving. | Import or dataset validation fails if missing. |
| optional | Useful when present but not required for serving. | Preserve when available. |
| known-issue-capable | Expected to be present unless upstream source lacks it in a documented way. | Store `status` and `issue` fields; validation fails if undocumented. |

## Domain Record Schemas

These are logical schemas. Implementation may use Pydantic models, dataclasses, or typed dictionaries, but response keys must remain compatible with these contracts.

### LawRecord

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `canonical_id` | required | string | Stable internal law ID. |
| `display_code` | required | string | User-facing abbreviation. |
| `display_name` | required | string | Human-readable law name. |
| `source` | required | SourceMetadata | Source provenance. |
| `aliases` | required | list[string] | Versioned aliases accepted by the registry. |
| `norm_count` | required | integer | Number of normalized norms. |
| `stand_date` | known-issue-capable | string/null | Source stand date or documented absence. |

### SourceMetadata

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `source_kind` | required | enum | `gesetze-im-internet` or `eur-lex-cellar`. |
| `source_identifier` | required | string | Source path or CELEX/Cellar identifier. |
| `source_url` | required | string | Canonical machine source URL. |
| `retrieved_at` | required | RFC 3339 string | Retrieval timestamp. |
| `stand_date` | known-issue-capable | string/null | Stand date when exposed. |
| `stand_date_status` | required | enum | `present`, `not_exposed`, or `known_issue`. |
| `stand_date_issue` | required when `stand_date_status=known_issue` | string/null | Machine-readable explanation for documented source limitations. |
| `content_hash` | required | string | SHA-256 of the raw source artifact. |
| `source_metadata` | optional | object | Source-kind-specific metadata such as German source path or EUR-Lex Cellar identifiers. |
| `known_issues` | optional | list[object] | Machine-readable source limitations. |

### Source-Kind Metadata

`SourceMetadata.source_metadata` must use stable keys per source kind:

| Source Kind | Required Keys | Notes |
|-------------|---------------|-------|
| `gesetze-im-internet` | `source_path` | Must match the path in `source-matrix.md`; aliases are not source paths. |
| `eur-lex-cellar` | `celex`, `cellar_work`, `expression`, `language`, `document` | For DSGVO Phase 1 these values are `32016R0679`, `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`, `0004.02`, `DE`, and `DOC_2`. |

### RawSnapshotRecord

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `snapshot_id` | required | string | Stable snapshot directory ID. |
| `canonical_id` | required | string | Law ID from the registry. |
| `source` | required | SourceMetadata | Provenance for the raw artifact. |
| `raw_path` | required | string | Path to the stored raw source artifact. |
| `bytes` | required | integer | Raw artifact size. |

### NormRecord

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `canonical_id` | required | string | Canonical citation ID such as `bgb/par:312`. |
| `law_id` | required | string | Parent law ID. |
| `norm_id` | required | string | Norm ID such as `par:312` or `art:246a`. |
| `unit` | required | enum | `par` or `art`. |
| `value` | required | string | Norm number/article value. |
| `title` | optional | string/null | Norm heading when available. |
| `text` | required unless `status=container` | string | Full text for text-bearing norms. |
| `status` | required | enum | `active`, `repealed`, `container`, or `known_issue`. |
| `url` | required | string | Stable public source URL for this norm or container. |
| `source` | required | SourceMetadata | Source provenance. |
| `subdivisions` | optional | list[SubdivisionRecord] | Parsed Absatz/Satz/Nummer/Buchstabe inventory. |
| `children` | optional | list[string] | Canonical child IDs for structural containers. |

### SubdivisionRecord

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `kind` | required | enum | `abs`, `satz`, `nr`, or `lit`. |
| `value` | required | string | Subdivision identifier. |
| `text` | required | string | Text for the subdivision. |
| `path` | required | string | Canonical subdivision path. |

### CitationSelection

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `requested_path` | required | string | Canonical subdivision path requested by the client. |
| `resolved_path` | required | string | Canonical subdivision path actually returned. |
| `subdivisions` | required | list[SubdivisionRecord] | Selected subdivision records in parent-to-child order. |
| `text` | required | string | Text for the most specific selected subdivision. |
| `known_issues` | optional | list[object] | Machine-readable limitations when fine-grained parsing is incomplete but documented. |

### ManifestRecord

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `dataset_id` | required | string | Dataset or raw snapshot package ID; Phase 2 raw manifests set this to `snapshot_id`. |
| `snapshot_id` | required | string | Raw snapshot directory ID for manifests under `data/sources/raw/{snapshot_id}/manifest.json`. |
| `created_at` | required | RFC 3339 string | Manifest creation time. |
| `entries` | required | list[RawSnapshotRecord] | Imported source records. |
| `hash_algorithm` | required | string | Must be `sha256` in Phase 1. |
| `validation` | required | object | Validation result summary. |

### CitationRequest

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `code` | required | string | User alias or canonical law ID. |
| `unit` | required | string | `par`, `section`, `§`, `art`, or `article`. |
| `paragraph_or_article` | required | string | Norm value. |
| `child_unit` | optional | string/null | Article child unit, if any. |
| `child_value` | optional | string/null | Article child value, if any. |
| `absatz` | optional | string/null | Absatz filter. |
| `satz` | optional | string/null | Satz filter. |
| `nummer` | optional | string/null | Nummer filter. |
| `buchstabe` | optional | string/null | Buchstabe filter. |

### CitationResponse

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `law` | required | LawRecord | Resolved law metadata. |
| `norm` | required | NormRecord | Resolved norm or child norm. |
| `selection` | optional | CitationSelection/null | Present only when Absatz/Satz/Nummer/Buchstabe filters are requested and resolved. |
| `citation` | required | object | Requested and canonical citation labels. |
| `source` | required | SourceMetadata | Source provenance. |

### SearchResult

| Field | Class | Type | Purpose |
|-------|-------|------|---------|
| `law_id` | required | string | Canonical law ID. |
| `law_display_code` | required | string | User-facing law abbreviation. |
| `law_display_name` | required | string | Human-readable law name. |
| `norm_id` | required | string | Norm ID. |
| `canonical_id` | required | string | Canonical citation ID. |
| `title` | optional | string/null | Norm title. |
| `snippet` | required | string | Plain-text bounded snippet. |
| `source` | required | SourceMetadata | Source provenance for the matched norm. |
| `url` | required | string | Norm URL. |
| `score` | required | number | Normalized public score in `[0.0, 1.0]`. |
| `highlight` | optional | object/null | Deliberately modeled markup or offsets; omitted by default. |

## Canonical Identifiers

| Entity | Grammar | Examples | Notes |
|--------|---------|----------|-------|
| Law ID | lowercase ASCII slug from the registry | `bgb`, `egbgb`, `uwg_2004`, `tdddg`, `bdsg_2018`, `pangv_2022`, `dsgvo_eu_2016_679` | Law IDs are stable internal identifiers, not necessarily source paths. |
| Source path | exact upstream path or source identifier | `bgbeg`, `ttdsg`, `pangv_2022`, `CELEX:32016R0679` | Source paths never come from free-form aliases. |
| Norm ID | `{unit}:{value}` with normalized lower unit | `par:312`, `par:5a`, `art:246a`, `art:5` | `par` represents `§`; `art` represents `Art.`. |
| Canonical citation ID | `{law_id}/{norm_id}` plus optional subdivision path | `bgb/par:312`, `egbgb/art:246a`, `uwg_2004/par:5a` | Subdivisions append as `abs:{n}/satz:{n}/nr:{n}/lit:{letter}` when requested. |
| HTTP norm path segment | URL-encoded canonical norm path with `/` encoded as `%2F` for child paths | `par%3A312`, `art%3A246a`, `art%3A246a%2Fpar%3A1` | HTTP may accept user shorthand, but responses must return canonical norm ID and canonical citation ID. |
| Article-plus-section child ID | `{law_id}/art:{article}/par:{section}` | `egbgb/art:246a/par:1` | Used for German source structures where an article container contains text-bearing `§` child entries. |

## Citation Request Rules

- `resolve_citation` accepts these structured fields: `code`, `unit`, `paragraph_or_article`, optional `child_unit`, optional `child_value`, optional `absatz`, optional `satz`, optional `nummer`, and optional `buchstabe`.
- `unit` must be one of `par`, `section`, `§`, `art`, or `article`; resolver output always uses `par` or `art`.
- `paragraph_or_article` accepts numbers with legal suffix letters such as `5a`, `246a`, and `312`.
- `child_unit` is only valid when `unit` resolves to `art`; Phase 1 supports `child_unit` values `par`, `section`, and `§`.
- `child_value` is required when `child_unit` is present and accepts legal section numbers with suffix letters.
- Absatz, Satz, Nummer, and Buchstabe are optional filters; missing filters return the full norm with parsed subdivision inventory when available.
- When Absatz, Satz, Nummer, or Buchstabe filters are provided and resolve successfully, `CitationResponse.selection` contains the selected subdivision path, ordered subdivision records, and selected text. `CitationResponse.norm` remains the full parent norm or child norm for provenance.
- A well-formed subdivision request for an existing norm that cannot be found returns `NORM_NOT_FOUND` with `error.details.missing_component="subdivision"`, `error.details.parent_norm_id`, and `error.details.subdivision_path`. Invalid subdivision hierarchy, such as requesting `satz` without `absatz`, returns `INVALID_CITATION`.
- Ranges such as `§§ 3 bis 6` are not valid Phase 1 resolver requests. They may appear as normalized repealed-range metadata but must return `INVALID_CITATION` when requested as an exact norm.
- Repealed or unavailable norms must be represented explicitly with status metadata if present in upstream source, not silently omitted.
- Structural article containers such as EGBGB `Art. 246a` return container metadata and child norm references. They do not aggregate child text. Text-bearing child sections are addressed as article-plus-section citations, for example canonical ID `egbgb/art:246a/par:1` or structured request `resolve_citation(code="EGBGB", unit="art", paragraph_or_article="246a", child_unit="par", child_value="1")`.
- MCP `resolve_citation` exposes `child_unit` and `child_value` as optional named parameters.
- HTTP `GET /laws/{code}/norms/{norm}` uses one `{norm}` path segment. For article-plus-section citations, encode the canonical norm path as `art%3A246a%2Fpar%3A1`, for example `/laws/egbgb/norms/art%3A246a%2Fpar%3A1`.

## Structured Error Payload

Every structured error response must include:

| Field | Purpose |
|-------|---------|
| `error.code` | One of the approved Phase 1 error codes. |
| `error.message` | Human-readable diagnostic. |
| `error.details` | Machine-readable context, including requested code/norm where applicable. |
| `error.suggestions` | Optional bounded list of alternatives; maximum 10 entries. |
| `error.source` | Optional source metadata when the failure is source-related. |

## Error Codes and Transport Mapping

| Error Code | HTTP Status | MCP Shape | Typical Cause |
|------------|-------------|-----------|---------------|
| `LAW_NOT_FOUND` | 404 | JSON object with `error` | Unknown law code or alias. |
| `NORM_NOT_FOUND` | 404 | JSON object with `error` | Law exists but requested norm or well-formed requested subdivision does not. |
| `AMBIGUOUS_LAW_ALIAS` | 409 | JSON object with `error` and `suggestions` | Alias maps to multiple candidates. |
| `SOURCE_UNAVAILABLE` | 503 | JSON object with `error` | Upstream source cannot be fetched or validated during import. |
| `DATASET_NOT_READY` | 503 | JSON object with `error` | Dataset failed validation or has not been loaded. |
| `INVALID_CITATION` | 422 | JSON object with `error` | Citation grammar or subdivision request is invalid. |
| `INVALID_QUERY` | 422 | JSON object with `error` | Search query is empty after normalization or cannot be safely executed. |

## Dataset Readiness Contract

Dataset readiness is a shared data-layer state, not an HTTP-only concept.

| State | Meaning | Serving Behavior |
|-------|---------|------------------|
| `ready` | Manifest, registry, normalized data, and search index are valid. | MCP and HTTP tools may serve requests. |
| `missing` | No configured dataset package exists. | Startup fails in strict mode; `/ready` returns `DATASET_NOT_READY` when an HTTP process is running for diagnostics. |
| `invalid` | Dataset package exists but validation failed. | Startup fails in strict mode; diagnostics expose validation failures. |
| `source_unavailable` | Import could not validate required upstream sources. | Import fails with `SOURCE_UNAVAILABLE`; existing ready dataset may continue only if explicitly configured. |

### Readiness Stage Contract

Phase 4 validates normalized dataset packages before a search index exists. To avoid marking an incomplete serving package as `ready`, readiness results must include a `stage` field:

| Stage | Required Components | Allowed State Before Later Phases |
|-------|---------------------|-----------------------------------|
| `normalized_dataset` | raw manifest, registry, normalized laws, normalized norms, source metadata, validation summary | `ready`, `missing`, `invalid`, `source_unavailable` for normalization-only consumers. |
| `serving_dataset` | all `normalized_dataset` components plus search index and transport-required indexes | `ready` only after Phase 6 creates a valid search index; before then, report `invalid` or `missing` with `details.search_index_status="pending"`. |

MCP and HTTP serving readiness must use `stage="serving_dataset"`. Phase 4 validators may emit `stage="normalized_dataset", state="ready"` only for downstream build phases.

## MCP Migration Decision

Phase 1 removes the old demo tool names from the stable tool surface. `get_lawlibrary` and `get_paragraph` are not exposed as stable Phase 1 tools. If temporary aliases are needed during implementation, they must be marked internal/deprecated and removed before Phase 9 release gate.

## MCP Tool Response Contracts

All MCP tools return JSON-compatible objects directly. They must not return pre-serialized JSON strings, plain-text error strings, or German guard messages.

| Tool | Success Shape | Notes |
|------|---------------|-------|
| `list_laws(query?: string)` | `{"laws": list[LawRecord], "count": integer, "query": string/null}` | `query` filters through registry/list metadata only; it does not search norm text. |
| `get_law(code: string)` | `{"law": LawRecord, "norms": list[object]}` | `norms` entries include `norm_id`, `canonical_id`, `unit`, `value`, `title`, `status`, and `url`; full norm text is returned by `get_norm` or `resolve_citation`. |
| `get_norm(code: string, norm: string)` | `CitationResponse` | `norm` accepts canonical norm paths such as `par:312`, `art:5`, and `art:246a/par:1`, plus simple `§ 312` and `Art. 5` shorthands. It rejects ranges and free-form prose with `INVALID_CITATION`. |
| `resolve_citation(...)` | `CitationResponse` | Exposes the structured citation fields from the Citation Request Rules, including `child_unit` and `child_value`. |
| `search_laws(query: string, codes?: list[string])` | `{"query": string, "codes": list[string]/null, "results": list[SearchResult], "count": integer}` | `query` is the normalized public query; `codes` contains canonical law IDs when a filter is supplied. |
| `get_source_metadata(code?: string)` | `{"sources": list[object], "count": integer}` | Each source entry includes `law_id`, `display_code`, `display_name`, and `source`. When `code` is provided, the list contains exactly one source or a structured law error. |

## HTTP API Contracts

HTTP endpoints are thin wrappers over the same service contracts as MCP. They return JSON objects and use the status codes from "Error Codes and Transport Mapping".

| Endpoint | Success Status | Success Shape | Notes |
|----------|----------------|---------------|-------|
| `GET /health` | 200 | `{"status": "ok"}` | Process health only; does not require a ready dataset. |
| `GET /ready` | 200 | readiness object | Returns 503 with `DATASET_NOT_READY` or `SOURCE_UNAVAILABLE` shape when the serving dataset is not ready. |
| `GET /laws?query=` | 200 | same as `list_laws` | Optional `query` filters law metadata. |
| `GET /laws/{code}` | 200 | same as `get_law` | `{code}` resolves through the registry. |
| `GET /laws/{code}/norms/{norm}` | 200 | `CitationResponse` | `{norm}` may be an encoded canonical norm path. Article-plus-section child path example: `/laws/egbgb/norms/art%3A246a%2Fpar%3A1`. |
| `GET /search?query=&codes=` | 200 | same as `search_laws` | `codes` is a repeatable query parameter; each value resolves through the registry. |
| `GET /openapi.json` | 200 | OpenAPI JSON | Must include all Phase 1 HTTP endpoints and schemas. |

Routes for norm lookup must preserve encoded child norm paths. Frameworks that decode `%2F` before route matching must use a path-capture route or equivalent so `art%3A246a%2Fpar%3A1` reaches the resolver as `art:246a/par:1`.

## Search Determinism Rules

- Query normalization must be explicit and tested: Unicode-normalize, trim whitespace, casefold, collapse internal whitespace, and tokenize into Unicode word tokens.
- The Phase 1 public query language is plain text. Query punctuation is not backend syntax; punctuation-only input produces no tokens and returns `INVALID_QUERY`.
- Multi-token queries use AND semantics over unique query tokens in first-seen order. A norm matches only when every query token appears at least once in the indexed title/text token stream.
- Empty or unsafe search queries must return `INVALID_QUERY`, not an empty success result.
- Default snippets must be plain text with a maximum length of 240 characters and ASCII `...` truncation when needed. Snippets are generated from the same indexed plain text, anchored at the earliest occurrence of the first matched query token in query order.
- Search returns at most 20 results by default unless a later transport phase deliberately models a limit parameter.
- For the deterministic Phase 1 token index, raw score is the sum of occurrence counts for all unique query tokens in the indexed title/text stream. The public `score` field is `raw_score / top_raw_score`, rounded to 6 decimal places, with the top hit in a result set set to `1.0`. If a different backend is used internally, it must preserve the same public scoring contract or map its ordered results to an equivalent deterministic formula.
- Result ordering must sort by score descending, then canonical law ID ascending, then norm ID ascending for ties.
- HTML highlighting is not part of the default response. Any highlight field must be separate from `snippet`.
