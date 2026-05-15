---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 1
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 1 - Manifest and corpus contract foundation

> Implements [Phase 1](../phases/phase-1.md) of [full-privacy-corpus](../plan.md)

## Approach

Add a versioned corpus manifest contract beside the existing normalized dataset model, without changing runtime serving behavior yet. The implementation should introduce typed source-family, terminal-state, provenance, source-limitation, canonical-ID-policy, and manifest validation helpers that later phases reuse. Validation should distinguish discovery manifests from terminal coverage manifests: discovery manifests may list unfetched sources, while terminal coverage manifests must assign every discovered source exactly one terminal state. Keep representative fixtures small and committed under `mcp/tests/fixtures/`, while generated full-corpus artifacts remain outside Git.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Add manifest contract code, validation tests, representative manifest fixtures, and a short docs note tying the manifest to source provenance. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/plan.md` | Defines global source families, terminal states, provenance matrix, and canonical ID rules. |
| `plans/full-privacy-corpus/phases/phase-1.md` | Gated scope and acceptance criteria for the manifest foundation. |
| `docs/features/source-provenance.md` | Current provenance fields and raw/normalized data separation to preserve. |
| `docs/features/law-loading-and-indexing.md` | Current package files and validation flow that later phases will connect to the manifest. |
| `mcp/legal_texts/models.py` | Existing `SourceKind`, `NormUnit`, `SourceMetadata`, and record dataclasses. |
| `mcp/legal_texts/validation.py` | Existing dataset validation entry point and source metadata checks. |
| `mcp/legal_texts/dataset.py` | Confirms the Phase 1 manifest is not yet wired into runtime package loading. |
| `mcp/legal_texts/importer.py` | Current snapshot manifest writer and source metadata shape. |
| `mcp/legal_texts/sources.py` | Current static source-family assumptions and GII/Cellar source metadata. |
| `mcp/legal_texts/registry.py` | Existing alias/collision semantics that inform but do not replace manifest ID policy. |
| `mcp/legal_texts/data/laws.v1.json` | Current hand-authored canonical IDs and aliases that migration examples must preserve. |
| `mcp/tests/test_dataset_validation.py` | Existing validation test style and fixture-ready dataset checks. |
| `mcp/tests/test_registry.py` | Existing alias and historical source-path regression cases to preserve. |
| `scripts/verify_release.py` | Release gate list that must remain compatible with fast fixture tests. |

## Implementation Steps

### Step 1: Introduce the corpus manifest model

- **What**: Create `mcp/legal_texts/manifest.py` with constants or typed literals for source families (`gii`, `eur-lex-cellar`, `state-law`, `third-party-scope`), terminal states (`imported`, `unsupported_format`, `source_unavailable`, `parse_failed`, `excluded_by_policy`), provenance requirements, helper validators, and a versioned manifest envelope.
- **Where**: New `mcp/legal_texts/manifest.py`; reuse `mcp/legal_texts/models.py` only where existing serving records need shared aliases.
- **Why**: Later GII, EUR-Lex, state-law, and relationship phases need one compatible manifest shape instead of source-specific ad hoc records.
- **Schema contract**: The top-level manifest must include `schema_version="corpus-manifest.v1"`, `dataset_id`, `package_id`, `created_at`, `validation_mode` (`discovery` or `terminal`), `generator` (`name` and `version`), `parser_versions` by source family, `discovered_sources`, `canonical_ids`, and `relationship_sources`; it may include `generated_package` metadata, `alias_migrations`, `generated_records`, and `source_limitations`. `canonical_ids` entries must contain `canonical_id`, `source_family`, `source_id`, and optional `aliases`. `relationship_sources` entries must contain `relationship_source_id`, `source_family`, `source_id`, `allowed_use`, and provenance/policy fields without creating legal-text `law_id` values. Optional `source_limitations` entries must reuse the same terminal-state names and source-family provenance fields as `discovered_sources`; do not define a parallel limitation schema in Phase 1. `generated_package` must reserve `schema_version`, `generated_at`, `record_counts`, `manifest_hash`, and `package_files` so Phase 2 can move the package contract into `package.json` without changing manifest semantics.
- **Considerations**: Keep serving `SourceKind` backwards compatible with existing values until Phase 2 expands package validation; do not force existing fixture `laws.json` and `norms.json` to include a full corpus manifest in this phase unless a representative manifest fixture is explicitly loaded by the new tests.

### Step 2: Add manifest validation rules

- **What**: Implement `validate_corpus_manifest(manifest: dict, *, require_terminal_states: bool | None = None) -> list[str]` and focused helpers that reject missing envelope fields, unsupported schema versions, invalid validation modes, duplicate discovered-source records, incomplete provenance, invalid generated-package metadata, invalid `excluded_by_policy` records, and missing terminal states when terminal coverage is required.
- **Where**: `mcp/legal_texts/manifest.py`; call from tests directly rather than wiring into `NormalizedDataset` yet.
- **Why**: Phase 1 acceptance requires contract validation before bulk discovery and package loading depend on it.
- **Validation-mode precedence**: `manifest["validation_mode"]` is authoritative. If `require_terminal_states` is `None`, derive terminal coverage from `validation_mode == "terminal"`. If callers pass a boolean and it conflicts with `validation_mode`, return a validation error instead of overriding the manifest. Add tests for `discovery`+`True`, `terminal`+`False`, omitted flag, and matching explicit flags.
- **Terminal-state requirements**: `imported` records require `canonical_id`, `source_url`, `content_sha256`, `retrieved_at`, `parser_version`, and at least one generated law or norm ID. `unsupported_format` requires `source_url`, `retrieved_at`, `content_type` or `format_hint`, and `reason`. `source_unavailable` requires `source_url`, `retrieved_at`, `http_status` or network error code, and `retryable`. `parse_failed` requires `source_url`, `retrieved_at`, `content_sha256` when content was fetched, `parser_version`, and diagnostic text. `excluded_by_policy` requires `policy_reason`, `policy_reference`, `decided_at`, and no copied third-party content.
- **Source-family provenance matrix**: Validate family-specific metadata in addition to terminal-state fields. `gii` records require `source_path`, `source_id="gii:<source_path>"`, `index_url`, `xml_zip_url` for official XML imports, `toc_url`, `toc_sha256` or discovery artifact ID, and status/stand-date metadata when present in the source. `eur-lex-cellar` records require `celex`, `language="de"`, `cellar_uri` or official EUR-Lex URL, selected work/expression/document metadata, consolidation/corrigenda policy, and version/retrieval hash. `state-law` records require `state_code`, `jurisdiction`, `official_source_url`, `source_format`, `adapter_class`, and limitation/adapter evidence. `third-party-scope` records require `provider`, `source_url`, robots/terms/policy review reference, allowed-use decision, target official record or source-limitation provenance, and an assertion that no editorial text is copied. Each row needs at least one positive and one missing-field negative test.
- **Considerations**: Treat required fields by `(source_family, terminal_state)` as data-driven tables so later source families can extend the matrix without rewriting validation flow. Phase 3 should write `validation_mode="discovery"` and call with `require_terminal_states=False`; Phase 4 and later coverage gates should write `validation_mode="terminal"` and call with `require_terminal_states=True` or omit the flag.

### Step 3: Define canonical ID and alias policy checks

- **What**: Add manifest-level `canonical_ids`, `alias_migrations`, and `relationship_sources` validation sections for deterministic law IDs, alias migrations, duplicate canonical IDs, and collision failures across GII, EUR-Lex, state-law, and relationship-source records.
- **Where**: `mcp/legal_texts/manifest.py`; reference current alias behavior in `mcp/legal_texts/registry.py`.
- **Why**: The plan requires ID/collision rules before bulk import phases start.
- **Required cases**: Reject duplicate canonical IDs, duplicate `(source_family, source_id)` discovered sources, CELEX records whose canonical IDs do not match their CELEX identifiers, state-law IDs without a `state:<state-code>/` prefix, and relationship-source records that try to create legal-text `law_id` values. Accept explicit alias migrations only when each record has `from_id`, `to_id`, `reason`, and `effective_from`.
- **Considerations**: Do not change `LawRegistry` behavior yet; this phase documents and validates the generated-corpus contract that later phases will integrate.

### Step 4: Add representative manifest fixtures

- **What**: Add small JSON fixtures under `mcp/tests/fixtures/manifest/` covering a complete valid terminal manifest plus focused invalid fixtures.
- **Where**: New fixture files under `mcp/tests/fixtures/manifest/`.
- **Why**: The manifest contract needs committed examples without importing the full corpus.
- **Required fixture coverage**: The valid fixture must include at least one `imported`, `unsupported_format`, `source_unavailable`, `parse_failed`, and `excluded_by_policy` record. Invalid fixtures must cover missing top-level envelope fields, duplicate source records, missing required fields for each terminal state, duplicate canonical IDs, invalid CELEX/canonical mismatch, missing state-law jurisdiction prefix, and a relationship-source record that creates a fake legal-text law ID.
- **Considerations**: Keep timestamps, hashes, parser versions, and generated record IDs deterministic in fixtures.

### Step 5: Add contract tests and documentation note

- **What**: Add `mcp/tests/test_corpus_manifest.py` for positive and negative manifest validation, and add it to `scripts/verify_release.py` so the release gate proves the new contract. Update `docs/features/source-provenance.md` with a concise manifest-contract note and terminal-state list.
- **Where**: `mcp/tests/test_corpus_manifest.py`; `docs/features/source-provenance.md`.
- **Why**: Tests prove invalid/incomplete manifest records fail, and docs establish the manifest as the completeness source of truth.
- **Considerations**: Existing fixture dataset tests in `mcp/tests/test_dataset_validation.py` must still pass unchanged.

## Testing Plan

Primary verify command: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`

Focused development command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_corpus_manifest.py mcp/tests/test_dataset_validation.py`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Unit | Manifest accepts representative valid imported, limitation, and policy-excluded records. | Validation returns no errors for complete terminal records. |
| Unit | Terminal validation covers every terminal state: `imported`, `unsupported_format`, `source_unavailable`, `parse_failed`, and `excluded_by_policy`. | Complete state-specific records pass; missing state-specific fields return actionable errors. |
| Unit | Validation rejects missing source IDs, terminal states, provenance, parser version, generated record IDs, duplicate discovered-source records, and malformed envelope/package metadata. | Validation returns actionable error strings. |
| Unit | Optional `source_limitations` entries reuse terminal-state and source-family provenance validation. | Limitation records cannot drift into a second incompatible schema. |
| Unit | Canonical ID policy rejects duplicate canonical IDs, CELEX/canonical mismatches, state-law IDs without jurisdiction, and relationship-source records that create legal-text law IDs. | Collision and policy failures are reported before later import phases use the manifest. |
| Unit | Source-family provenance matrix accepts and rejects required GII, EUR-Lex/Cellar, state-law, and third-party-scope fields. | Missing family-specific provenance fails even when generic terminal-state fields are present. |
| Unit | `validation_mode` and `require_terminal_states` mismatch cases are rejected. | Discovery and terminal manifests cannot be silently validated under the wrong mode. |
| Unit | Discovery-mode validation accepts unfetched discovered-source records while still rejecting duplicates and missing source IDs. | Phase 3 discovery artifacts can validate before Phase 4 assigns terminal states. |
| Regression | Existing normalized fixture dataset validation and release gate still pass. | `scripts/verify_release.py` includes the manifest contract tests and existing E2E checks. |

### Test Integrity Constraints

- `mcp/tests/test_dataset_validation.py` must remain semantically unchanged except for additive assertions if needed; existing fixture readiness cannot be weakened.
- Existing fixture `mcp/tests/fixtures/normalized/` records must not be edited merely to satisfy the new manifest tests.
- New manifest tests must use explicit invalid fixtures instead of mutating production-like fixtures at runtime.

## Rollback Strategy

Remove `mcp/legal_texts/manifest.py`, `mcp/tests/test_corpus_manifest.py`, the new manifest fixtures, and the source-provenance docs note. Existing runtime loading should remain unaffected because the manifest contract is not wired into serving startup in this phase.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Manifest storage encoding for committed fixtures | Single JSON file; several focused JSON files | Several focused JSON files | Smaller fixtures make negative cases clearer and avoid implying a full generated corpus is committed. |
| Runtime enforcement timing | Enforce in Phase 1; defer package enforcement to Phase 2 | Defer package enforcement to Phase 2 | Phase 1 defines and tests the contract; Phase 2 owns generated package compatibility. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/models.py` | `SourceKind`, `NormUnit`, `SourceMetadata` | Current serving records only know GII and EUR-Lex and only `par`/`art`. |
| `mcp/legal_texts/validation.py` | `validate_dataset_package`, `validate_laws`, `validate_norms`, `_validate_source` | Existing validation is normalized-record focused and has no manifest terminal-state model. |
| `mcp/legal_texts/dataset.py` | `NormalizedDataset.__init__` | Current runtime does not consume a corpus manifest; Phase 2 will wire generated packages. |
| `mcp/legal_texts/importer.py` | `import_snapshot`, `RawSnapshotEntry`, `source_metadata` | Current manifest is a raw snapshot list over `SOURCE_SPECS`, not a complete discovered-source corpus manifest. |
| `mcp/legal_texts/sources.py` | `SOURCE_SPECS`, `GERMAN_SOURCES`, `SourceSpec` | Current source family is static and fixture-sized. |
| `mcp/legal_texts/registry.py` | `LawRegistry.validate` | Existing alias collision behavior is useful but not enough for generated source-family ID rules. |
| `mcp/legal_texts/data/laws.v1.json` | canonical IDs and aliases | Alias migration examples must preserve existing hand-authored IDs rather than invent replacements. |
| `mcp/tests/test_dataset_validation.py` | Fixture readiness tests | Confirms Phase 1 must not break existing normalized fixture loading. |

### Mismatches / Notes

- Current `SourceKind` does not include state-law or third-party scope families; keep the broader manifest source-family vocabulary separate until Phase 2 expands package support.
- Current raw snapshot `manifest.json` records downloaded `SOURCE_SPECS` entries only and does not encode discovery-mode versus terminal-coverage validation.
- Existing validation checks source metadata on laws/norms, but not discovered-source coverage, source limitations, or policy exclusions.
- Current `validate_dataset_package` checks only normalized package files (`laws.json`, `norms.json`, optional `search-index.json`) and does not validate the versioned corpus manifest or generated-package metadata introduced here.
- The existing release gate may run live source-matrix checks depending on environment; Phase 1 acceptance should use `SKIP_LIVE_SOURCE_MATRIX=true` to keep the manifest contract gate fixture-backed.
