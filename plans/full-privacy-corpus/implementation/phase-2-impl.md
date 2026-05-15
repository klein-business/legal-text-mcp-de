---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 2
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 2 - Generated package format and runtime compatibility

> Implements [Phase 2](../phases/phase-2.md) of [full-privacy-corpus](../plan.md)

## Approach

Extend the normalized serving package contract from the current four-file fixture layout into a generated corpus package layout that can include `package.json` corpus metadata, a Phase 1 manifest, source limitations, and relationship records. Keep existing `laws.json`, `norms.json`, `readiness.json`, and `search-index.json` behavior backwards compatible, and add citation-unit support in validation before later parsers emit new units.

Strict generated-package validation is opt-in by file presence: legacy fixture packages without `package.json` continue through the current validation path, while any package containing `package.json` is treated as generated and must pass the new strict contract before runtime loading reports ready.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Extend dataset validation/loading contracts, add package fixtures, add relationship schema validation, and preserve MCP/HTTP fixture behavior. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-1.md` | Phase 2 builds on the manifest contract and terminal states. |
| `plans/full-privacy-corpus/implementation/phase-1-impl.md` | Defines planned `mcp/legal_texts/manifest.py` names and fixture strategy. |
| `plans/full-privacy-corpus/phases/phase-2.md` | Gated generated-package scope and acceptance criteria. |
| `docs/features/law-loading-and-indexing.md` | Current package contract and runtime loading flow. |
| `mcp/legal_texts/models.py` | Current `NormUnit` and serving record dataclasses. |
| `mcp/legal_texts/validation.py` | Existing `validate_dataset_package`, law/norm source validation, and readiness logic. |
| `mcp/legal_texts/dataset.py` | Current `NormalizedDataset` loader and lookup indexes. |
| `mcp/legal_texts/runtime.py` | Runtime readiness responses that must surface generated-package validation failures. |
| `mcp/legal_texts/normalizer.py` | Current generated fixture writer and `readiness.json` production path. |
| `mcp/legal_texts/resolver.py` | Existing resolver unit parsing and `par`/`art` assumptions. |
| `scripts/verify_e2e.py` | Existing local MCP/HTTP E2E gate required by Phase 2 acceptance. |
| `scripts/verify_release.py` | Release gate wrapper that should keep generated package tests and E2E checks passing. |
| `mcp/tests/test_http_api.py` | Current HTTP backwards compatibility expectations. |
| `mcp/tests/test_mcp_tools.py` | Current stable MCP tool list and response contract. |
| `docs/features/law-loading-and-indexing.md` | Documentation target for generated package and citation-unit schemas. |
| `docs/features/source-provenance.md` | Documentation target for source-limitation and relationship provenance schemas. |

## Implementation Steps

### Step 1: Define generated package metadata and optional files

- **What**: Add a package contract for `package.json`, `manifest.json`, `source-limitations.json`, and `relationships.json` while preserving the current required `laws.json`, `norms.json`, `readiness.json`, and serving `search-index.json`.
- **Where**: `mcp/legal_texts/validation.py` for validation; new fixtures under `mcp/tests/fixtures/generated_package/`.
- **Why**: Future generated datasets need source failures and relationships without creating fake law/norm records.
- **Schema contract**: `package.json` must include `schema_version="generated-package.v1"`, `dataset_id`, `package_id`, `generated_at`, `generator` (`name`, `version`), `manifest_path`, `readiness_path`, `record_counts` (`laws`, `norms`, `relationships`, `source_limitations`, `discovered_sources`, `imported_sources`), `content_hashes` for package files, `validation_mode`, and `source_families`. `content_hashes` must exclude `package.json` itself; test this explicitly to avoid self-hash ambiguity. `manifest.json` must validate through Phase 1 `validate_corpus_manifest`. `source-limitations.json` must contain objects with `limitation_id`, `source_family`, `source_id`, `terminal_state`, `source_url`, `retrieved_at` or `decided_at`, `reason`, `details`, and optional `http_status`, `content_type`, `policy_reference`, `retryable`, and `parser_version`. `relationships.json` must contain objects with `relationship_id`, `relationship_type`, `subject` (`kind`, `id`), `object` (`kind`, `id`), `source_family`, `source_id`, `provenance` (`basis`, `source_url`, optional `retrieved_at`), and optional `metadata`.
- **Considerations**: Current fixture packages without `package.json` must still load through the legacy path. Current code does not require or consume `readiness.json`; Phase 2 should validate it when present in generated packages but must not claim existing startup already depends on it.

### Step 2: Add additive citation-unit validation

- **What**: Expand allowed generated-record norm units to include `recital`, `chapter`, `section`, `annex`, and `container` for package validation, while keeping resolver behavior for existing `par`/`art` unchanged until later phases add runtime support.
- **Where**: `mcp/legal_texts/models.py` `NormUnit`; `mcp/legal_texts/validation.py` `validate_norms`.
- **Why**: Phase 5 and later parsers need package validation to accept new citation units.
- **Considerations**: Do not route generated-record unit validation through the existing `normalize_unit` helper until its behavior is deliberately changed; today `normalize_unit("section")` maps to `par`. `status="container"` remains distinct from `unit="container"`; validation should reject malformed combinations rather than silently accepting arbitrary units.

### Step 3: Validate manifest and normalized-record consistency

- **What**: Add generated-package validation that checks imported manifest records reference generated law/norm IDs, source limitations do not require fake laws, relationship targets resolve to official records or limitations, and package metadata counts match actual records.
- **Where**: `mcp/legal_texts/validation.py`; call Phase 1 `validate_corpus_manifest` from `mcp/legal_texts/manifest.py`.
- **Why**: Acceptance requires package validation to fail when manifest and normalized records disagree.
- **Prerequisite check**: Before implementing this step, verify that Phase 1 landed `mcp/legal_texts/manifest.py` with `validate_corpus_manifest(manifest, *, require_terminal_states: bool | None = None)`. If the symbol name or signature changed during Phase 1 implementation, update this Phase 2 plan artifact before coding rather than adapting silently.
- **Loader integration**: Add `validate_generated_package(path: Path, *, require_search_index: bool = False) -> list[str]` and have `validate_dataset_package` detect `package.json`. If `package.json` is absent, preserve the legacy path. If it is present, run strict generated-package validation before returning success. `NormalizedDataset.__init__` should therefore reject invalid generated packages but keep legacy fixtures compatible. `LegalTextRuntime` readiness should surface the first strict validation errors for generated packages.
- **Considerations**: Keep the existing `validate_dataset_package(path, stage=...)` behavior stable for legacy packages; strict mode is automatic only for generated packages that declare `package.json`.

### Step 4: Add relationship record schema validation

- **What**: Validate `relationships.json` records for stable IDs, supported relationship types, provenance, source IDs, target official records, and target source limitations.
- **Where**: New `mcp/legal_texts/relationships.py` or package-validation helpers in `mcp/legal_texts/validation.py`; fixtures under `mcp/tests/fixtures/generated_package/`.
- **Why**: Phase 2 owns relationship package schema even though Phase 11 owns runtime relationship APIs.
- **Relationship types**: Support only `references`, `implements`, `amends`, `repeals`, `supplements`, `same_subject_as`, `source_scope_link`, and `limitation_for` until a later phase adds more. Targets may be `law`, `norm`, or `source_limitation` only in Phase 2. Third-party or unimported external material may appear only as relationship provenance/source metadata or as a `source_limitation` target, never as an unresolved `external_source` target. Reject duplicate `relationship_id`, unknown type, missing provenance, relationship records with copied third-party editorial text, unresolved external targets, and targets that do not exist in generated laws/norms/source limitations.
- **Considerations**: Relationship records must not contain copied third-party editorial text; keep fields metadata-only.

### Step 5: Preserve runtime and transport behavior

- **What**: Update tests so the existing fixture package still passes through `NormalizedDataset`, `LegalTextRuntime`, MCP tools, and HTTP endpoints, while a generated-package fixture exercises strict validation and readiness reporting.
- **Where**: `mcp/tests/test_generated_package.py`; existing `mcp/tests/test_resolver.py`, `mcp/tests/test_http_api.py`, `mcp/tests/test_mcp_tools.py`.
- **Why**: Package changes are additive and must not regress current `par` and `art` behavior.
- **Considerations**: Do not add new MCP/HTTP tools in this phase; Phase 11 owns runtime exposure.

### Step 6: Document generated package schemas

- **What**: Document the generated package layout, citation-unit additions, source-limitation schema, relationship schema, target-resolution rules, and `package.json` content-hash rule.
- **Where**: `docs/features/law-loading-and-indexing.md` for package/citation-unit/readiness semantics; `docs/features/source-provenance.md` for source limitations, relationship provenance, and the rule that relationship targets resolve only to official records or source limitations in Phase 2.
- **Why**: Phase 2 deliverables require documented schemas, not only code-level validation.
- **Considerations**: Documentation must state that legacy fixture packages without `package.json` remain supported and that generated packages are strict when `package.json` is present.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`

Focused development command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_generated_package.py mcp/tests/test_dataset_validation.py mcp/tests/test_resolver.py mcp/tests/test_http_api.py mcp/tests/test_mcp_tools.py && PYTHONPATH=mcp uv run --group dev python scripts/verify_e2e.py`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Unit | Strict generated-package validation accepts coherent metadata, manifest, source limitations, and relationships. | Validation returns ready or no errors. |
| Unit | Package validation rejects bad manifest references, malformed units, duplicate relationships, missing relationship provenance, unresolved relationship targets, malformed readiness files, and mismatched package counts/hashes. | Validation returns explicit errors. |
| Unit | Relationship validation rejects any `external_source` target that is not represented as an official record or source limitation. | Phase 2 target-resolution acceptance cannot be bypassed by unresolved external targets. |
| Unit | Package hash validation excludes `package.json` from `content_hashes`. | Self-hash behavior is deterministic and documented. |
| Runtime | `NormalizedDataset` rejects invalid generated packages when `package.json` is present and still loads legacy fixtures when absent. | Strict packages cannot be served with invalid metadata; current fixture package remains ready. |
| Docs | Generated package, citation-unit, relationship, and source-limitation schemas are documented in the chosen feature docs. | Schema changes are discoverable by implementers and users. |
| E2E | Local MCP and HTTP E2E checks run against the fixture package after package-contract changes. | Existing transport behavior remains unchanged. |
| Regression | Existing runtime, MCP, HTTP, and resolver fixtures still behave as before. | Existing tests pass with unchanged API responses. |

### Test Integrity Constraints

- Existing `mcp/tests/test_mcp_tools.py::test_tool_registry_has_only_supported_tools` must remain authoritative; do not add Phase 11 tools here.
- Existing `mcp/tests/test_resolver.py` assertions for `par`, `art`, and EGBGB child citations must remain unchanged.
- Do not weaken `validate_norms` source requirements to make generated-package fixtures pass.
- Do not disable, skip, xfail, or weaken existing tests unless a specific Phase 2 requirement demands an assertion update and the replacement assertion preserves the original behavior boundary.

## Rollback Strategy

Revert generated-package validation helpers, optional package fixtures, relationship schema validation, and expanded unit validation. Existing four-file fixture loading should return to the Phase 1 behavior.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Strict package validation entry point | Extend `validate_dataset_package`; add separate helper | Add `validate_generated_package` and invoke it from `validate_dataset_package` when `package.json` exists | Current runtime uses `validate_dataset_package` at startup; generated packages must fail fast while legacy fixtures remain compatible. |
| Relationship target encoding | Canonical norm IDs only; canonical law or norm IDs plus source limitations | Canonical law or norm IDs plus source limitations | Phase 2 acceptance requires relationship targets to resolve to official records or source limitations. |
| Package metadata filename | `package.json`; `corpus-package.json` | `package.json` | Short, conventional, and used consistently by later runtime and gate plans. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/validation.py` | `validate_dataset_package`, `validate_norms`, `_validate_source` | Current package validation only checks required files and record source fields. |
| `mcp/legal_texts/models.py` | `NormUnit = Literal["par", "art"]` | New units are currently unsupported by type aliases and resolver normalization. |
| `mcp/legal_texts/dataset.py` | `NormalizedDataset.__init__` | Startup loading currently validates files then reads laws/norms; it does not consume readiness metadata. |
| `mcp/legal_texts/runtime.py` | readiness helpers | Runtime readiness is synthesized from loaded dataset state and needs explicit generated-package error reporting. |
| `mcp/legal_texts/normalizer.py` | `write_normalized_dataset` | Existing fixture generation writes `readiness.json`, but validation/loading currently do not require it. |
| `mcp/legal_texts/resolver.py` | `CANONICAL_NORM_RE`, `normalize_unit` usage | Resolver currently parses only exact `par`/`art` forms. |
| `mcp/tests/test_mcp_tools.py` | Stable tool list assertion | Confirms Phase 2 must not add runtime APIs. |

### Mismatches / Notes

- `docs/features/law-loading-and-indexing.md` documents only `laws.json`, `norms.json`, `readiness.json`, and `search-index.json`; Phase 2 needs docs or fixtures to introduce optional generated-package files.
- Current package validation checks `laws.json`, `norms.json`, and optionally `search-index.json`; it does not require or parse `readiness.json`. Phase 2 must add strict generated-package validation for `readiness.json` when `package.json` declares a generated package, while preserving legacy behavior.
- Current `normalize_unit("section")` maps to `par`; generated-record unit validation must avoid accidentally rewriting first-class `section` records.
- `http_models.SourceMetadataResponse` exists but `mcp/http_api.py` currently does not expose a source metadata HTTP endpoint; this remains a Phase 11 runtime-surface issue, not Phase 2 scope.
- `docs/features/law-loading-and-indexing.md` currently documents only the legacy serving package; Phase 2 must add generated-package schema docs there and source-limitation/relationship provenance docs in `docs/features/source-provenance.md`.
