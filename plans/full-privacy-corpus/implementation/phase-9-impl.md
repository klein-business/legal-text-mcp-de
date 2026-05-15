---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 9
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 9 - German state-law machine-readable and HTML adapters

> Implements [Phase 9](../phases/phase-9.md) of [full-privacy-corpus](../plan.md)

## Approach

Implement state-law adapters only for Phase 8 inventory records classified as `machine_readable` or `stable_html`. Emit normalized law/norm records with jurisdiction-encoded canonical IDs and official source provenance, or convert a state to an explicit source limitation if implementation proves infeasible.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Add machine-readable/HTML state-law adapters, fixtures, validation, and citation ID tests. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-9.md` | Gated adapter scope. |
| `plans/full-privacy-corpus/implementation/phase-8-impl.md` | Inventory file and adapter class source of truth. |
| `plans/full-privacy-corpus/implementation/phase-2-impl.md` | Generated-package files and validation contract for imported records and source limitations. |
| `mcp/legal_texts/data/state_law_sources.v1.json` | Phase 8 inventory data file that defines eligible `machine_readable`/`stable_html` states. |
| `mcp/legal_texts/data/state_law_limitations.v1.json` | Phase 8 limitation artifact used when eligible states become limitations. |
| `mcp/legal_texts/state_law_inventory.py` | Planned inventory validation and adapter class API. |
| `mcp/legal_texts/manifest.py` | State-law terminal-state and provenance validation. |
| `mcp/legal_texts/gii_xml.py` | Useful parsing/subdivision patterns for German legal XML/HTML text. |
| `mcp/legal_texts/normalizer.py` | Current normalization orchestration to extend for state-law records. |
| `mcp/legal_texts/models.py` | Norm/law record shape and source metadata conventions. |
| `mcp/legal_texts/validation.py` | Unit/source validation for generated package records. |
| `mcp/tests/test_state_law_inventory.py` | Inventory outcomes that drive adapter selection. |
| `mcp/tests/test_generated_package.py` | Generated-package contract tests for imported/limited state-law outcomes. |

## Implementation Steps

### Step 0: Validate Phase 8 inventory inputs

- **What**: Load `mcp/legal_texts/data/state_law_sources.v1.json` and `mcp/legal_texts/data/state_law_limitations.v1.json`, validate them with the Phase 8 helpers, and derive the exact eligible set of states whose `adapter_class` is `machine_readable` or `stable_html`.
- **Where**: `mcp/legal_texts/state_law_inventory.py`; `mcp/tests/test_state_law_adapters.py`.
- **Why**: Phase 9 scope is determined by Phase 8 inventory data, not by hand-picked parser fixtures.
- **Considerations**: Fail fast when the inventory is missing, incomplete, has dangling limitation references, or when no eligible state set can be derived.

### Step 1: Add state-law adapter interfaces

- **What**: Create `mcp/legal_texts/state_law.py` with a small adapter protocol/result type for imported records and source limitations.
- **Where**: New `mcp/legal_texts/state_law.py`.
- **Why**: Machine-readable and HTML adapters need one output contract before PDF handling in Phase 10.
- **Contract**: Adapter results must carry `state_code`, `source_id`, `law_id`, `norms`, `source_metadata`, `terminal_state`, `parser_version`, and optional `source_limitation`. Imported results must be convertible to Phase 2 generated-package records; failed results must be convertible to Phase 1 source limitations.
- **Considerations**: Output law IDs must follow `state:<state-code>/<stable-law-slug>` and must not collide with GII or EUR-Lex IDs.

### Step 2: Implement machine-readable adapters from inventory

- **What**: For states classified as `machine_readable`, add parser functions that consume official XML/JSON or equivalent machine-readable source and emit validated laws/norms.
- **Where**: `mcp/legal_texts/state_law.py` or source-specific helpers under `mcp/legal_texts/`.
- **Why**: These are preferred official sources and should be imported before PDF/unstructured handling.
- **Considerations**: Use source metadata fields for jurisdiction, source format, official URL, retrieval timestamp, hash, parser version, and terminal state; parser selection must come from inventory fields.

### Step 3: Implement stable HTML adapters from inventory

- **What**: For states classified as `stable_html`, add deterministic HTML extraction based on stable semantic selectors or structure recorded in the inventory.
- **Where**: `mcp/legal_texts/state_law.py`; fixtures under `mcp/tests/fixtures/state_law/`.
- **Why**: HTML sources are in Phase 9 scope when the inventory classifies them as stable.
- **Considerations**: Do not parse unstable website chrome as legal text; stable selectors or structural assumptions must be recorded in or validated against the inventory. If selectors are not stable, emit a limitation instead.

### Step 4: Write generated-package and manifest outcomes

- **What**: Convert adapter results into Phase 2 generated-package records: state-law `laws.json`/`norms.json` additions for imported states, Phase 1 terminal manifest states, `source-limitations.json` entries for infeasible eligible states, and package count/hash updates.
- **Where**: `mcp/legal_texts/state_law.py`; `mcp/legal_texts/validation.py`; generated-package fixtures under `mcp/tests/fixtures/generated_package/`.
- **Why**: Phase 10 and Phase 11 need persisted imported-or-limited outcomes, not only adapter return values.
- **Considerations**: Produce or update a `state_law_adapter_outcomes.v1` summary with `state_code`, `adapter_class`, `terminal_state`, `law_id` or `source_limitation_id`, source artifact hash, and package record references.

### Step 5: Add fixtures and validation tests

- **What**: Add representative machine-readable and HTML fixtures, canonical ID tests, provenance tests, and collision tests.
- **Where**: `mcp/tests/test_state_law_adapters.py`; fixture package updates as needed.
- **Why**: Acceptance requires every eligible state to import or record a justified limitation.
- **Considerations**: Do not handle PDF-only states here; Phase 10 owns them.

### Step 6: Add opt-in real-source adapter verification

- **What**: Add `scripts/verify_state_law_adapters.py` that reads the Phase 8 inventory, processes only `machine_readable` and `stable_html` states, writes a generated package or package fragment, validates imported-or-limited outcomes, and persists evidence.
- **Where**: New script under `scripts/`; tests with fake fetches in `mcp/tests/test_state_law_adapters.py`.
- **Why**: Official state portals may change; Phase 9 needs current imported-or-limited evidence outside default PR CI.
- **Command**: `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_adapters.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --limitations mcp/legal_texts/data/state_law_limitations.v1.json --package-dir .artifacts/state-law/package --output .artifacts/state-law/adapter-gate.json`
- **Considerations**: Keep this opt-in and artifact-backed; do not add live portal fetches to default release.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_state_law_adapters.py mcp/tests/test_state_law_inventory.py mcp/tests/test_dataset_validation.py mcp/tests/test_generated_package.py mcp/tests/test_corpus_manifest.py`

Opt-in adapter verification command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_adapters.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --limitations mcp/legal_texts/data/state_law_limitations.v1.json --package-dir .artifacts/state-law/package --output .artifacts/state-law/adapter-gate.json`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Preflight | Phase 8 inventory files exist, validate, and derive the eligible machine-readable/stable-HTML state set. | Parser work cannot proceed from ad hoc state selection. |
| Parser | Machine-readable and stable HTML fixtures emit normalized records. | Records validate with state-law provenance. |
| ID policy | State canonical IDs encode jurisdiction and avoid GII/EUR-Lex collisions. | Collision tests fail invalid IDs. |
| Manifest | Infeasible eligible states become explicit source limitations. | No eligible state is silently omitted. |
| Package | Imported or limited Phase 9 state outcomes validate against Phase 1 manifest and Phase 2 generated-package rules. | State-law records are usable by Phase 10/11 without schema drift. |
| Gate | Opt-in adapter gate writes imported-or-limited evidence for eligible official sources. | Current official-source outcomes are persisted outside default CI. |

### Test Integrity Constraints

- Do not add PDF parser tests or manual transcription fixtures in Phase 9.
- Do not weaken `test_state_law_inventory.py`; adapter outcomes must follow the inventory.
- State-law fixture text must come from official source fixtures or minimal synthetic parser fixtures clearly marked as such.
- Do not downgrade a Phase 8 `machine_readable` or `stable_html` state to a limitation without recording the implementation evidence and limitation reason.

## Rollback Strategy

Remove state-law adapter code, fixtures, tests, and normalization integration for machine-readable/HTML states. Phase 8 inventory remains intact for future retry.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| State-law ID prefix | Bare slug; `state:<state-code>/<slug>` | `state:<state-code>/<slug>` | The plan requires jurisdiction encoding and collision prevention. |
| HTML parser fallback | Best-effort text scrape; source limitation | Source limitation | Avoid serving website chrome or unstable extracted text as law. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/gii_xml.py` | `_subdivisions`, `_content_text` | Existing German law parsing helpers can inspire state-law normalization. |
| `mcp/legal_texts/normalizer.py` | `normalize_snapshot` | Current normalizer only dispatches GII or DSGVO by source kind. |
| `mcp/legal_texts/models.py` | `LawRecord`, `NormRecord`, `SourceMetadata` | State-law outputs must match serving record shape. |
| `mcp/legal_texts/validation.py` | `_validate_source` | Needs state-law provenance validation from Phase 2/8. |

### Mismatches / Notes

- Current code has no HTML parsing dependency beyond standard library XML; if robust HTML parsing needs a dependency, implementation must update `pyproject.toml` intentionally.
- Current registry loading from `laws.v1.json` does not include generated state-law aliases; generated package loading may need registry extension or package-local law lookup support.
- Current baseline lacks `mcp/legal_texts/state_law_inventory.py` and Phase 8 data files until Phase 8 lands; Phase 9 must verify these prerequisites before implementation.
- Current `normalize_snapshot` does not write state-law generated-package records; Phase 9 must add the package/manifest integration path rather than relying on legacy normalization.
