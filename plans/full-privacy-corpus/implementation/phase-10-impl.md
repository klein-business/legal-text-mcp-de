---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 10
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 10 - German state-law PDF adapters and source limitations

> Implements [Phase 10](../phases/phase-10.md) of [full-privacy-corpus](../plan.md)

## Approach

Close state-law coverage for Phase 8 records not handled by Phase 9. Implement PDF extraction only where official source stability and extraction quality satisfy the manifest/provenance contract; otherwise record explicit source limitations. After this phase, every one of 16 states must be imported or limited.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Add PDF adapter or limitation handling, negative tests, and state-law coverage summary. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-10.md` | Gated PDF/limitation scope and no-manual-transcription rule. |
| `plans/full-privacy-corpus/implementation/phase-2-impl.md` | Generated-package files, `source-limitations.json`, manifest consistency, and package counts. |
| `plans/full-privacy-corpus/implementation/phase-8-impl.md` | Inventory classes and remaining state outcomes. |
| `plans/full-privacy-corpus/implementation/phase-9-impl.md` | Adapter result contract and imported/limited state outputs. |
| `mcp/legal_texts/data/state_law_sources.v1.json` | Phase 8 inventory data file that defines PDF and limitation-only states. |
| `mcp/legal_texts/data/state_law_limitations.v1.json` | Phase 8 limitation records that Phase 10 must preserve or extend. |
| `mcp/legal_texts/state_law_inventory.py` | Inventory API for remaining states. |
| `mcp/legal_texts/state_law.py` | Planned adapter/result contract from Phase 9. |
| `mcp/legal_texts/manifest.py` | Source limitation and terminal-state validation. |
| `mcp/legal_texts/validation.py` | Generated package validation for imported records and limitations. |
| `mcp/tests/test_state_law_adapters.py` | Existing state-law adapter test patterns to extend. |
| `mcp/tests/test_generated_package.py` | Generated-package validation tests that must cover final state-law limitations. |

## Implementation Steps

### Step 0: Verify prerequisite artifacts

- **What**: Before implementation, verify Phase 1, Phase 2, Phase 8, and Phase 9 outputs exist with the planned names or update this plan before coding.
- **Where**: `mcp/legal_texts/manifest.py`, `mcp/legal_texts/state_law_inventory.py`, `mcp/legal_texts/state_law.py`, `mcp/legal_texts/data/state_law_sources.v1.json`, `mcp/legal_texts/data/state_law_limitations.v1.json`, and the Phase 9 `state_law_adapter_outcomes.v1` summary or equivalent generated-package outcome source.
- **Why**: These files are prerequisite outputs, not baseline repo anchors.
- **Considerations**: Do not infer prior phase outcomes from tests alone; consume validated data/package artifacts.

### Step 1: Identify remaining Phase 8 states

- **What**: Add a coverage helper that merges Phase 9 imported/limited outcomes with Phase 8 inventory and lists remaining `pdf` or `limitation_only` states.
- **Where**: `mcp/legal_texts/state_law.py`; `mcp/tests/test_state_law_coverage.py`.
- **Why**: Acceptance requires all 16 states to have an imported or limitation outcome after Phases 9 and 10.
- **Inputs**: Consume `mcp/legal_texts/data/state_law_sources.v1.json`, `mcp/legal_texts/data/state_law_limitations.v1.json`, and Phase 9 `state_law_adapter_outcomes.v1` or validated generated-package records as the source of truth for machine-readable/HTML states.
- **Contract**: The helper must produce persisted `state_law_coverage.v1` with exactly 16 entries, each entry containing `state_code`, `adapter_class`, `terminal_state`, `law_id` or `source_limitation_id`, and provenance/evidence links.
- **Considerations**: Do not reprocess machine-readable/HTML states already handled in Phase 9 except to read their outcome.

### Step 2: Implement PDF extraction only for approved cases

- **What**: Add a PDF adapter for one supported extraction class if official source stability, text extraction quality, content hash, extraction method, and parser version can be recorded.
- **Where**: `mcp/legal_texts/state_law_pdf.py` or `mcp/legal_texts/state_law.py`; fixtures under `mcp/tests/fixtures/state_law/`.
- **Why**: PDF support is in scope only when the manifest/provenance contract can be met.
- **Quality gate**: PDF extraction may be marked imported only if tests prove deterministic text extraction, no manual transcription, source hash capture, extraction method/version capture, and normalized record validation. Otherwise emit `unsupported_format` or `parse_failed` limitation as appropriate.
- **Considerations**: If adding a PDF library is necessary, update dependencies and tests intentionally; otherwise use source limitations.

### Step 3: Add source limitation records for unsupported states

- **What**: Emit limitation records for unstructured, unstable, unsupported, or limitation-only states with official URL, reason, timestamp, and source-family provenance.
- **Where**: `mcp/legal_texts/manifest.py` helpers, `source-limitations.json`, `manifest.json`/`source_limitations`, `package.json` counts, and state-law coverage output.
- **Why**: The plan forbids pretending every state has equally parseable official text.
- **Package contract**: Every Phase 10 limitation must be present in Phase 2 `source-limitations.json`, referenced from the terminal manifest, counted in `package.json`, and represented in `state_law_coverage.v1`.
- **Considerations**: No state-law text may be manually transcribed or invented.

### Step 4: Add coverage summary and negative tests

- **What**: Add tests proving unsupported PDFs/unstructured sources are visible limitations and that final state-law coverage has exactly 16 imported-or-limited outcomes.
- **Where**: `mcp/tests/test_state_law_pdf_and_limitations.py`; `mcp/tests/test_state_law_coverage.py`.
- **Why**: Phase 11 runtime coverage APIs need final state-law coverage data.
- **Considerations**: Keep generated full state-law data outside Git; commit only representative fixtures and limitations.

### Step 5: Add opt-in PDF/source evidence gate

- **What**: Add `scripts/verify_state_law_pdf_sources.py` that reads Phase 8/9 state-law artifacts, probes/fetches remaining PDF/unstructured official sources, records content hashes, extraction method/version, import-or-limitation outcome, and validates generated-package consistency.
- **Where**: New script under `scripts/`; fake-fetch tests under `mcp/tests/test_state_law_pdf_and_limitations.py`.
- **Why**: Phase 10 import-versus-limitation decisions depend on current official source stability and extraction quality, not only fixtures.
- **Command**: `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_pdf_sources.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --phase9-outcomes .artifacts/state-law/adapter-gate.json --package-dir .artifacts/state-law/package --output .artifacts/state-law/pdf-gate.json`
- **Considerations**: Keep this opt-in and outside default release; Phase 10 completion needs a current artifact or archived equivalent when real official-source decisions are claimed.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_state_law_pdf_and_limitations.py mcp/tests/test_state_law_coverage.py mcp/tests/test_state_law_adapters.py mcp/tests/test_generated_package.py mcp/tests/test_corpus_manifest.py`

Opt-in PDF/source verification command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_pdf_sources.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --phase9-outcomes .artifacts/state-law/adapter-gate.json --package-dir .artifacts/state-law/package --output .artifacts/state-law/pdf-gate.json`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Preflight | Phase 1/2/8/9 prerequisite artifacts exist and match the planned file/symbol names. | Execution fails fast instead of relying on non-existent baseline anchors. |
| Coverage | All 16 states have imported or source-limitation outcomes after Phases 9 and 10. | Coverage summary has no missing states. |
| PDF | Supported PDF fixture records source URL, hash, extraction method, parser version, and normalized records. | Records validate or limitation is emitted. |
| Package | Final state-law coverage validates against manifest/generated-package rules. | Phase 11 can load imported records and source limitations. |
| Gate | Opt-in PDF/source gate writes official-source evidence for remaining states. | Import/limitation decisions are backed by current or archived artifacts. |
| Negative | Unsupported, unstable, or unstructured sources become limitations. | No manual or fake legal text is produced. |

### Test Integrity Constraints

- Do not manually transcribe state-law text in fixtures or generated outputs.
- Do not weaken Phase 9 adapter tests when a state moves to limitation; update only if Phase 8 inventory outcome or implementation evidence justifies it.
- Source limitation records must preserve official source provenance and reason.

## Rollback Strategy

Remove PDF adapter code, limitation generation for remaining states, coverage summary tests, and PDF fixtures. Phase 9 imported/limited state outcomes remain intact.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| PDF extraction dependency | Add dedicated dependency; no PDF adapter unless existing stack suffices | No PDF adapter unless quality/dependency decision is justified during implementation | Phase scope permits PDF only when stable and provenance-complete. |
| Limitation granularity | One summary record; one record per state/source | One record per state/source | Runtime coverage and validation bundle need per-state outcomes. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/state_law_inventory.py` | Planned Phase 8 inventory records | Determines which states are PDF or limitation-only. |
| `mcp/legal_texts/state_law.py` | Planned Phase 9 adapter result contract | Phase 10 must merge with Phase 9 outcomes. |
| `mcp/legal_texts/manifest.py` | Planned source limitation helpers | Unsupported state sources must be explicit, queryable outcomes. |
| `mcp/legal_texts/validation.py` | Generated package validation | Final imported-or-limited state-law coverage must validate. |

### Mismatches / Notes

- The current repository has no PDF extraction code or dependency.
- Phase 10 cannot guarantee a PDF adapter will be implemented; the gated scope explicitly allows source limitations when extraction quality or stability is insufficient.
- Current baseline lacks `mcp/legal_texts/manifest.py`, `mcp/legal_texts/state_law_inventory.py`, `mcp/legal_texts/state_law.py`, and state-law tests until prior phases land; Phase 10 must verify prerequisite artifacts before coding.
- Current generated-package validation is planned in Phase 2; Phase 10 must write final source limitations and coverage into that contract rather than only helper-local summaries.
