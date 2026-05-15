---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 4
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 4 - GII bulk normalization and coverage gates

> Implements [Phase 4](../phases/phase-4.md) of [full-privacy-corpus](../plan.md)

## Approach

Convert Phase 3 discovered GII source records into normalized law/norm records where parseable, while assigning every discovered GII source exactly one terminal manifest state. Reuse the current GII parser for fixture compatibility, extend it only for representative structural variants, and add explicit release-blocking evidence for BDSG and TDDDG.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Add bulk GII import orchestration, parser variant fixtures, terminal-state coverage gate, and critical-law checks. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-4.md` | Gated bulk normalization scope and critical-law acceptance criteria. |
| `plans/full-privacy-corpus/implementation/phase-1-impl.md` | Terminal-state manifest contract and `validate_corpus_manifest` requirements. |
| `plans/full-privacy-corpus/implementation/phase-2-impl.md` | Generated-package validation helper and package schema that Phase 4 must satisfy. |
| `plans/full-privacy-corpus/implementation/phase-3-impl.md` | Discovery manifest inputs and `mcp/legal_texts/gii_toc.py` outputs. |
| `mcp/legal_texts/manifest.py` | Phase 1 validator and terminal-state constants used by the coverage gate. |
| `mcp/legal_texts/gii_toc.py` | Phase 3 discovery record and artifact schema consumed by bulk normalization. |
| `mcp/legal_texts/gii_xml.py` | Current `parse_gii_zip` behavior and supported structural patterns. |
| `mcp/legal_texts/normalizer.py` | Current `normalize_snapshot` loop from manifest entries to laws/norms. |
| `mcp/legal_texts/importer.py` | Current raw snapshot writing, hashing, and source metadata. |
| `mcp/legal_texts/registry.py` | Existing registry alias/collision behavior for generated law IDs. |
| `mcp/legal_texts/validation.py` | Law/norm source validation and generated-package validation from Phase 2. |
| `mcp/legal_texts/dataset.py` | Generated package load path used to prove critical-law records are servable. |
| `mcp/legal_texts/resolver.py` | Critical-law resolution evidence for BDSG and TDDDG. |
| `mcp/tests/test_corpus_manifest.py` | Earlier-phase terminal-state contract tests that must remain compatible. |
| `mcp/tests/test_generated_package.py` | Earlier-phase package-contract tests that must remain compatible. |
| `mcp/tests/test_normalizer_gii.py` | Existing GII parser fixture tests. |
| `docs/features/supported-laws.md` | Current BDSG/TDDDG source identifiers and aliases. |

## Implementation Steps

### Step 1: Add bulk GII normalization orchestration

- **What**: Add a bulk import function that consumes Phase 3 GII manifest records, downloads each `xml.zip`, records source metadata, parses parseable payloads, writes normalized records plus terminal manifest states, and validates the terminal manifest through `validate_corpus_manifest(..., require_terminal_states=True)`.
- **Where**: `mcp/legal_texts/importer.py` for fetching/state classification; `mcp/legal_texts/normalizer.py` for normalization orchestration.
- **Why**: Phase 4 acceptance requires every discovered GII source to become imported or an explicit failure state.
- **Generated registry**: Before normalization, build a generated GII registry from Phase 3 discovery metadata. Each discovery record becomes a law candidate keyed by normalized GII `source_path`; existing curated IDs and aliases (`tdddg` for source path `ttdsg`, `bdsg_2018`, `egbgb`, `pangv_2022`, etc.) must be preserved through explicit migration/alias entries. Validate duplicate law IDs, duplicate source paths, and alias collisions before any payload is parsed. `normalize_snapshot` must accept this generated registry or a generated law-record map instead of requiring every discovery item to exist in the static `LawRegistry`.
- **Terminal-state artifact**: Imported records must reference generated law/norm IDs and parser version. Failure records must use the Phase 1 required fields for `unsupported_format`, `source_unavailable`, or `parse_failed`. Do not use `excluded_by_policy` for parser failures.

### Step 2: Extend GII parser variant coverage

- **What**: Add fixture ZIPs or inline XML fixtures for representative GII structural patterns, including paragraph laws, article containers with child paragraphs, annex-like structures, repealed/empty norms, and title-only containers.
- **Where**: `mcp/legal_texts/gii_xml.py`; `mcp/tests/test_gii_bulk_normalization.py`; existing `mcp/tests/test_normalizer_gii.py`.
- **Why**: Bulk import needs parser regression coverage wider than the current two tests.
- **Expected outputs**: Define a fixture-backed parser-variant matrix at `docs/features/gii-parser-variant-matrix.md` or `mcp/tests/fixtures/gii/parser-variant-matrix.json`. The matrix must state expected `unit`, `norm_id`, `status`, URL suffix, `children`, and `text`/`None` behavior for paragraph laws, article-child paragraphs, annexes (`unit="annex"`), sections (`unit="section"`), structural containers (`unit="container"`, `status="container"`), repealed norms (`status="repealed"` or empty text with explicit status), and title-only containers.
- **Considerations**: Parser variants are regression coverage, not proof of full corpus completeness.

### Step 3: Generate stable canonical IDs and provenance

- **What**: Ensure GII law IDs use Phase 1 source-path rules, preserve current aliases where present, and fail validation on collisions without an explicit migration entry.
- **Where**: New generated registry helper in `mcp/legal_texts/registry.py` or `mcp/legal_texts/gii_registry.py`; `mcp/legal_texts/validation.py`.
- **Why**: Acceptance requires stable canonical IDs and provenance for imported GII records.
- **Generated-package linkage**: The generated registry helper must emit law records and alias metadata in the Phase 2 generated-package format, then run package validation before `NormalizedDataset` or resolver tests load it.
- **Considerations**: Existing IDs such as `bdsg_2018`, `tdddg`, `egbgb`, and `pangv_2022` must remain resolvable through current aliases.

### Step 4: Add terminal-state and critical-law gates

- **What**: Add `scripts/verify_gii_corpus_gate.py` that consumes a discovery/import artifact and verifies exactly one terminal state per discovered GII source, generated-package validation success, parser-variant matrix consistency, plus BDSG and TDDDG imported-and-resolvable evidence or release-blocking upstream limitations.
- **Where**: New script under `scripts/`; tests under `mcp/tests/test_gii_bulk_normalization.py`.
- **Why**: Full-discovery terminal-state coverage and critical named privacy-law checks are explicit DoD items.
- **CLI contract**: `scripts/verify_gii_corpus_gate.py --discovery-artifact <path> --package-dir <path> --output <path>` must write `schema_version="gii-corpus-gate.v1"`, discovered/imported/terminal-state counts, validation errors, critical-law evidence for BDSG/TDDDG, parser-variant matrix version, and generated-package path/hash. A non-network fixture mode may use committed fixtures; live/full-discovery runs remain explicit or scheduled.
- **Critical-law exception rule**: BDSG/TDDDG may satisfy the gate only as imported-and-resolvable official GII records or as release-blocking upstream source limitations (`source_unavailable` with official upstream evidence, or equivalent documented upstream non-availability). Reachable `parse_failed` and `unsupported_format` outcomes must fail the critical-law gate because they represent implementation/parser gaps, not acceptable upstream limitations.
- **Considerations**: Generated full-corpus output stays ignored and is not committed.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_gii_bulk_normalization.py mcp/tests/test_normalizer_gii.py mcp/tests/test_registry.py mcp/tests/test_resolver.py mcp/tests/test_corpus_manifest.py mcp/tests/test_generated_package.py`

Opt-in full-discovery gate command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_gii_corpus_gate.py --discovery-artifact .artifacts/gii-discovery/latest.json --package-dir .artifacts/gii-corpus/package --output .artifacts/gii-corpus/gate.json`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Parser | Representative GII ZIP structures produce expected law/norm records. | Norm IDs, units, containers, children, and provenance validate. |
| Manifest | Imported, unavailable, unsupported, and parse-failed GII sources receive exactly one terminal state. | Coverage gate rejects missing or duplicate terminal states. |
| Package | Phase 4 generated registry and terminal-state artifacts pass Phase 1 manifest and Phase 2 generated-package validation. | Incompatible terminal states or package metadata fail before serving. |
| Gate | `scripts/verify_gii_corpus_gate.py` validates fixture artifacts and writes persisted evidence. | Missing full-discovery terminal states or invalid critical-law evidence fail the gate. |
| Critical law | BDSG and TDDDG fixture/generated records resolve from GII provenance, and reachable parser failures or unsupported formats are rejected as critical-law exceptions. | Resolver returns records or test fixture records release-blocking upstream source limitation only. |

### Test Integrity Constraints

- Existing `mcp/tests/test_normalizer_gii.py` expectations for `par:5` and `art:246a/par:1` must remain valid.
- Do not change current alias behavior in `mcp/tests/test_registry.py` except for additive generated-registry coverage.
- Tests must not mark parse failures as policy exclusions.

## Rollback Strategy

Remove bulk GII orchestration, parser-variant fixtures/tests, and the GII corpus gate script. Existing fixture GII parser and static-source snapshot import remain intact.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Full corpus artifact location | Commit fixtures only; commit generated corpus | Commit fixtures only | The plan requires full generated datasets to stay outside Git. |
| Critical-law failure classification | Ordinary limitation; release-blocking limitation | Release-blocking limitation | BDSG and TDDDG are explicitly critical named GII privacy laws. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/gii_xml.py` | `parse_gii_zip`, `PAR_RE`, `ART_RE`, `_subdivisions` | Current parser supports basic `par` and article-child patterns only. |
| `mcp/legal_texts/normalizer.py` | `normalize_snapshot` | Current normalizer assumes every manifest entry resolves through `LawRegistry` and parses successfully. |
| `mcp/legal_texts/importer.py` | `import_snapshot` | Current importer raises on source failures instead of recording terminal states per discovered source. |
| `docs/features/supported-laws.md` | TDDDG/BDSG rows and alias rules | Current docs identify required GII source paths `ttdsg` and `bdsg_2018`. |

### Mismatches / Notes

- Current normalizer has no per-entry failure handling; a parse exception can stop the whole run.
- Current parser does not explicitly support `annex`, `section`, or generic structural container units added in Phase 2.
- Current `normalize_snapshot` resolves every manifest entry through the static `LawRegistry`; most Phase 3 discovered GII entries will fail unless Phase 4 adds the generated-registry path described above.
- `mcp/legal_texts/manifest.py`, `mcp/legal_texts/gii_toc.py`, and generated-package validation are Phase 1-3 prerequisite outputs, not baseline files before those phases execute.
