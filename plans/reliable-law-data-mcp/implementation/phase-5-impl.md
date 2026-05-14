---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 5
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 5 - Citation Resolver

> Implements [Phase 5](../phases/phase-5.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 5 adds a transport-independent citation resolver over the Phase 4 normalized dataset and Phase 3 registry. It should resolve exact structured requests into `CitationResponse` JSON-compatible objects, return structured errors for invalid/missing/ambiguous input, and write golden JSON for every required fixture. It must not parse free-form legal prose, infer missing text, or perform legal evaluation.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| `mcp/legal_texts/resolver.py` | create | Citation request validation, law resolution, norm lookup, subdivision slicing, and response/error construction. |
| `mcp/legal_texts/dataset.py` | create/modify | Loader/index for normalized dataset packages produced by Phase 4. |
| `mcp/legal_texts/models.py` | modify | Finalize `CitationRequest`, `CitationResponse`, and canonical citation helpers. |
| `mcp/legal_texts/errors.py` | modify | Add/verify `NORM_NOT_FOUND` and `INVALID_CITATION` plus reuse registry errors. |
| `mcp/tests/test_resolver.py` | create | Resolver unit tests for exact hits, aliases, child citations, subdivisions, and errors. |
| `mcp/tests/golden/citations/` | create/modify | Golden JSON responses and error payloads for required citations. |
| `docs/features/law-loading-and-indexing.md` | modify/reference | Document resolver service boundary if feature docs need a cross-link. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global resolver, structured error, fixture, and no-hallucination requirements. |
| `plans/reliable-law-data-mcp/phases/phase-5.md` | Gated Phase 5 scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | Citation request/response grammar, norm IDs, article-plus-section rules, subdivision paths, and error payloads. |
| `plans/reliable-law-data-mcp/fixture-inventory.md` | Required golden citation set and EGBGB child grammar. |
| `plans/reliable-law-data-mcp/implementation/phase-3-impl.md` | Registry behavior, suggestions, ambiguity semantics, and alias normalization. |
| `plans/reliable-law-data-mcp/implementation/phase-4-impl.md` | Normalized record shape, EGBGB container/child data, readiness stage, and fixtures. |
| `mcp/legal_texts/registry.py` | Phase 3 law identity service consumed by resolver. |
| `mcp/legal_texts/validation.py` | Phase 4 readiness/validation behavior that gates resolver dataset loading. |
| `mcp/legal_texts/data/laws.v1.json` | Actual committed registry artifact used by resolver tests for canonical IDs, aliases, and source metadata. |
| `mcp/tests/fixtures/normalized/` | Normalized dataset fixtures used by resolver tests. |
| `mcp/tests/conftest.py` | Existing pytest fixture style. |

## Resolver Contract

`resolve_citation(code, unit, paragraph_or_article, child_unit=None, child_value=None, absatz=None, satz=None, nummer=None, buchstabe=None)` must:

- resolve `code` through the registry and preserve canonical law metadata in responses;
- normalize `unit` to `par` or `art`;
- reject invalid units, missing values, ranges such as `§§ 3 bis 6`, child fields without article parent, child unit without child value, and subdivision filters that skip required parent levels;
- construct canonical norm paths such as `par:312`, `art:5`, or `art:246a/par:1`;
- look up normalized records by canonical ID from the validated normalized dataset;
- return container metadata and children for EGBGB `art:246a`;
- return text-bearing child data for `art:246a/par:1`;
- return requested Absatz/Satz/Nummer/Buchstabe selections in `CitationResponse.selection` while preserving the full parent `norm`;
- return `NORM_NOT_FOUND` with `error.details.missing_component="subdivision"`, `error.details.parent_norm_id`, and `error.details.subdivision_path` when an existing norm lacks a well-formed requested subdivision;
- never fabricate missing norm text, source metadata, URLs, or legal meaning.

## Implementation Steps

### Step 1: Add Dataset Lookup Layer

- **What**: Add a normalized dataset loader/index that exposes law metadata, norm lookup by canonical ID, child norm lookup, and readiness checks.
- **Where**: `mcp/legal_texts/dataset.py`.
- **Why**: Resolver should not know file layout details or re-parse raw XML.
- **Considerations**: Require `stage="normalized_dataset", state="ready"` from Phase 4 validation. If dataset is missing or invalid, return/raise `DATASET_NOT_READY`; do not return empty successes. Tests must include at least one resolver integration path that loads the normalized fixture package through this dataset layer rather than constructing all records in memory.

### Step 2: Implement Citation Request Validation

- **What**: Validate units, values, child fields, ranges, and subdivision filter hierarchy before doing norm lookup.
- **Where**: `mcp/legal_texts/resolver.py` and `mcp/legal_texts/models.py`.
- **Why**: Bad citation shapes must return `INVALID_CITATION` rather than fall through to missing norm behavior.
- **Considerations**: `child_unit` is valid only for article parents and supports `par`, `section`, and `§`; `child_value` is required when `child_unit` is set. Suffix values like `5a` are valid; ranges are invalid exact citations.

### Step 3: Resolve Law Aliases Through Registry

- **What**: Use Phase 3 `resolve_law` behavior for `code`, preserving `LAW_NOT_FOUND` and `AMBIGUOUS_LAW_ALIAS` errors and bounded suggestions.
- **Where**: `mcp/legal_texts/resolver.py`.
- **Why**: Citation behavior must use the same law identity layer as import, search, MCP, and HTTP.
- **Considerations**: Tests should cover alias inputs such as `UWG`, `TTDSG`, `tddsg`, `BDSG`, `pangv`, `DSGVO`, and canonical IDs.

### Step 4: Implement Norm and Child Norm Lookup

- **What**: Construct canonical norm IDs and citation IDs, then retrieve matching normalized records.
- **Where**: `mcp/legal_texts/resolver.py`.
- **Why**: Exact citations must resolve deterministically from normalized records.
- **Considerations**: Missing law uses registry errors; existing law with missing norm returns `NORM_NOT_FOUND` with requested law, norm, canonical law ID, and suggestions if available. EGBGB `Art. 246a` returns container metadata; `Art. 246a § 1` uses child path `art:246a/par:1`.

### Step 5: Implement Subdivision Selection

- **What**: Filter response content to requested Absatz/Satz/Nummer/Buchstabe when deterministic subdivision records exist.
- **Where**: `mcp/legal_texts/resolver.py`.
- **Why**: Phase 5 must support precise accesses below norm level without guessing.
- **Considerations**: Invalid subdivision shapes return `INVALID_CITATION`. Well-formed subdivision requests for an existing norm that are absent return `NORM_NOT_FOUND` with `missing_component="subdivision"`, `parent_norm_id`, and `subdivision_path` details. Successful subdivision requests return `CitationResponse.selection` with `requested_path`, `resolved_path`, ordered selected subdivision records, selected text, and known-issue metadata when relevant. Preserve full norm text on `CitationResponse.norm`.

### Step 6: Write Golden JSON Fixtures

- **What**: Create golden responses for every citation in `fixture-inventory.md`, including representative subdivision requests and error fixtures.
- **Where**: `mcp/tests/golden/citations/`.
- **Why**: Later MCP and HTTP tests should compare against the same service-level expectations.
- **Considerations**: Include BGB `§ 312`, `§ 355`, `§ 309`; EGBGB container and child; DDG `§ 5`; UWG `§ 3`, `§ 5`, `§ 5a`, `§ 5b`, `§ 7`; TDDDG `§ 25`, `§ 26`; BDSG `§ 1`, `§ 22`, `§ 26`, `§ 34`, `§ 35`; BFSG `§ 1`; VSBG `§ 36`; PAngV `§ 1`, `§ 4`, `§ 5`; DSGVO `Art. 5`, `Art. 6`, `Art. 12`, `Art. 13`, `Art. 14`, `Art. 15`, `Art. 17`, `Art. 21`, `Art. 25`, `Art. 32`, `Art. 82`. Subdivision goldens must assert `selection` without replacing full `norm` provenance.

### Step 7: Add Resolver Error Tests

- **What**: Test `LAW_NOT_FOUND`, `AMBIGUOUS_LAW_ALIAS`, `NORM_NOT_FOUND`, `INVALID_CITATION`, and `DATASET_NOT_READY` resolver paths.
- **Where**: `mcp/tests/test_resolver.py` and `mcp/tests/golden/citations/errors/`.
- **Why**: Clients need machine-readable recovery paths and no silent empty responses.
- **Considerations**: Ambiguity should reuse the Phase 3 explicit non-validating registry test path; production registry stays collision-free.

### Step 8: Document Resolver Service Boundary

- **What**: Document that resolver is a shared service consumed by future MCP/HTTP phases and not yet an MCP tool migration.
- **Where**: `docs/features/law-loading-and-indexing.md` or a new resolver feature doc if existing docs become too broad.
- **Why**: Avoid claiming transport availability before Phase 7/8.
- **Considerations**: Keep legal-advice and free-form parsing non-goals explicit.

## Testing Plan

Primary verify command:

```bash
PYTHONPATH=mcp python3 -m pytest mcp/tests/test_resolver.py mcp/tests/test_normalizer_gii.py mcp/tests/test_normalizer_eurlex.py mcp/tests/test_dataset_validation.py mcp/tests/test_registry.py mcp/tests/test_source_import.py mcp/tests/test_source_matrix.py mcp/tests/test_parser.py mcp/tests/test_library.py
```

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Required citation goldens | Every fixture-inventory citation resolves to canonical law/norm/source JSON. | Golden JSON matches exactly except explicitly ignored volatile fields. |
| EGBGB article-plus-section | `Art. 246a` container and structured `Art. 246a § 1` request with `child_unit="par"`, `child_value="1"`. | Container returns children; child returns text-bearing norm. |
| Dataset-loader integration | Resolve representative citations through a dataset loaded from `mcp/tests/fixtures/normalized/`. | Dataset package layout, readiness validation, registry metadata, and resolver lookup work together. |
| Alias inputs | Required aliases resolve through registry before norm lookup. | Responses include canonical law ID, display code, source kind, and URL. |
| Subdivision lookup | Absatz/Satz/Nummer/Buchstabe requests over deterministic normalized fixtures. | `selection.requested_path`, `selection.resolved_path`, ordered selected subdivisions, and selected text match golden JSON; unsafe parsing preserves known issues. |
| Invalid citation grammar | Ranges, invalid units, child without article parent, missing child value, and skipped subdivision hierarchy. | `INVALID_CITATION` structured errors. |
| Missing law/norm/subdivision | Unknown law aliases, missing norms, and well-formed missing subdivisions. | `LAW_NOT_FOUND` or `NORM_NOT_FOUND` with requested context, `missing_component` details for subdivisions, and suggestions where applicable. |
| Dataset readiness | Missing/invalid normalized dataset used by resolver. | `DATASET_NOT_READY`, not empty success. |
| Existing prior-phase tests | Source import, registry, and normalizer behavior remain passing. | Earlier tests still pass. |

### Test Integrity Constraints

- Do not disable, skip, xfail, delete, or weaken Phase 2-4 tests or existing legacy parser/library tests to make resolver tests pass.
- Golden JSON must include canonical ID, display code, display name, source metadata, URL, title where present, text/status, citation labels, and known-issue metadata where relevant.
- Resolver tests must use normalized fixtures, not raw XML or legacy Markdown parser output.

## Rollback Strategy

Remove `mcp/legal_texts/resolver.py`, resolver-specific dataset helpers if unused, resolver model/error additions, `mcp/tests/test_resolver.py`, resolver golden fixtures, and resolver documentation updates. Phase 2-4 data/import/normalization artifacts remain intact.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Free-form citations | parse strings / structured only / LLM-assisted | structured only | Phase 1 requires no hallucination or legal interpretation. |
| Missing subdivision code | `NORM_NOT_FOUND` / `INVALID_CITATION` / new error code | invalid shape = `INVALID_CITATION`; absent well-formed subdivision = `NORM_NOT_FOUND` with `missing_component="subdivision"` details | Keeps approved error code set while preserving deterministic recovery context. |
| Resolver output granularity | always full norm / filtered text for requested subdivision / both | include requested subdivision plus source norm metadata | Precise access should not hide provenance or parent norm context. |
| Runtime transport | expose MCP now / HTTP now / service only | service only | Phase 7 and Phase 8 own transports. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/parser.py` | `LawLibrary.get` and `LawParser.get_paragraph` | Existing lookup is paragraph/string based and not suitable for structured citations. |
| `mcp/server.py` | legacy MCP tools | Transport migration is intentionally deferred. |
| `plans/reliable-law-data-mcp/contracts.md` | citation grammar and error payloads | Defines resolver request/response behavior. |
| `plans/reliable-law-data-mcp/fixture-inventory.md` | required citations | Defines golden coverage. |
| `plans/reliable-law-data-mcp/implementation/phase-4-impl.md` | normalized records and readiness | Resolver must consume normalized data, not raw sources. |
| `mcp/legal_texts/data/laws.v1.json` | committed registry artifact | Resolver tests should exercise the real registry data created by Phase 3. |

### Mismatches / Notes

- The current repository has no resolver service; Phase 5 adds it as a new shared domain layer.
- MCP `get_paragraph` may still exist until Phase 7; Phase 5 should not expose or preserve it as the new resolver API.
- Any missing or ambiguous subdivision data must be represented as structured errors or known-issue metadata rather than guessed text.
