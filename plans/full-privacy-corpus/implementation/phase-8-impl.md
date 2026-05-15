---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 8
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 8 - German state-law source family inventory

> Implements [Phase 8](../phases/phase-8.md) of [full-privacy-corpus](../plan.md)

## Approach

Add an explicit inventory data model for all 16 German state privacy-law source outcomes before implementing parsers. Each state receives official source candidates, format classification, adapter assignment, reachability/stability evidence, and a source limitation where no usable official source exists.

The fixed state set is `BW`, `BY`, `BE`, `BB`, `HB`, `HH`, `HE`, `MV`, `NI`, `NW`, `RP`, `SL`, `SN`, `ST`, `SH`, and `TH`; validation must reject missing, duplicate, or unknown state codes.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | create/modify | Add state-law inventory data, validation helpers, fixtures, and source-family documentation. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-8.md` | Gated inventory-only state-law scope. |
| `plans/full-privacy-corpus/implementation/phase-1-impl.md` | Manifest limitation and provenance contract. |
| `mcp/legal_texts/manifest.py` | Planned source-family and terminal-state validation. |
| `mcp/legal_texts/sources.py` | Existing source specification pattern to avoid overloading for inventory-only state sources. |
| `mcp/legal_texts/validation.py` | Generated package/source limitation validation. |
| `docs/features/source-provenance.md` | Provenance fields to extend for state-law source-family constraints. |

## Implementation Steps

### Step 1: Add state-law inventory schema

- **What**: Create `mcp/legal_texts/state_law_inventory.py` with validation for 16 state records, state code, state name, official source candidates, source format, adapter class, reachability evidence, and limitation references.
- **Where**: New `mcp/legal_texts/state_law_inventory.py`.
- **Why**: Later adapter phases must consume stable inventory outcomes instead of rediscovering source availability.
- **Schema contract**: Each inventory record must include `state_code`, `state_name`, `law_slug`, derived or stored `law_id="state:<state-code>/<stable-law-slug>"`, `official_sources` (`url`, `format`, `publisher`, optional `content_hash`), `adapter_class` (`machine_readable`, `stable_html`, `pdf`, `limitation_only`), `reachability` (`checked_at`, `status`, `content_type`, optional `hash`), `stability_note`, and `source_limitation_id` when adapter class is `limitation_only`.
- **ID helper**: Add `derive_state_law_id(state_code, law_slug)` and validate that stored IDs, when present, match the helper and the fixed state-code set.
- **Considerations**: Inventory state codes must be normalized and cannot collapse cross-state aliases into one law ID.

### Step 2: Add committed inventory data

- **What**: Add `mcp/legal_texts/data/state_law_sources.v1.json` with one record per German state and adapter class values `machine_readable`, `stable_html`, `pdf`, or `limitation_only`.
- **Where**: New data file under `mcp/legal_texts/data/`.
- **Why**: Acceptance requires every German state to have an explicit inventory outcome.
- **Limitation artifact**: Add the committed Phase 8 limitation artifact `mcp/legal_texts/data/state_law_limitations.v1.json` with Phase 1-compatible limitation records. Every `limitation_only` inventory record must reference an existing limitation ID in this file; dangling references and incomplete limitation provenance must fail validation. Embedded limitations are not the planned artifact shape for Phase 8 because later phases and gate scripts consume the separate file.
- **Considerations**: Use source limitations for unknown/unstable cases instead of leaving records incomplete; every limitation must validate against Phase 1 state-law provenance requirements.

### Step 3: Add reachability and stability check hooks

- **What**: Add an opt-in script or helper for reachability checks that records timestamp, URL, status/content type, and content hash where fetchable.
- **Where**: New `scripts/verify_state_law_inventory.py` and tests with fake fetches.
- **Why**: The phase requires reachability/stability checks without making PR CI network-heavy.
- **Command contract**: `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_inventory.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --limitations mcp/legal_texts/data/state_law_limitations.v1.json --write-artifact .artifacts/state-law/inventory-reachability.json` must write `schema_version="state-law-inventory-reachability.v1"`, one result per non-`limitation_only` state/source, `checked_at`, status or error, content type, content hash where fetchable, and stability classification.
- **Acceptance evidence**: Phase 8 completion must include either a current `.artifacts/state-law/inventory-reachability.json` produced by this command or a current externally archived equivalent with artifact path and SHA-256 hash recorded in the phase handover. A merely scheduled future run is incomplete work and cannot satisfy Phase 8 completion.
- **Considerations**: Fast tests must use fixtures/fake fetches; live checks are explicit or externally archived and stay outside default release.

### Step 4: Add validation tests and docs note

- **What**: Add `mcp/tests/test_state_law_inventory.py` proving exactly 16 outcomes, valid adapter classes, provenance, and limitation records.
- **Where**: New tests; update `docs/features/source-provenance.md` or a new docs note for state-law constraints.
- **Why**: Prevents later state-law phases from hiding missing source decisions.
- **Considerations**: Do not implement full state-law parsing in this phase.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_state_law_inventory.py mcp/tests/test_corpus_manifest.py`

Opt-in reachability command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_state_law_inventory.py --inventory mcp/legal_texts/data/state_law_sources.v1.json --limitations mcp/legal_texts/data/state_law_limitations.v1.json --write-artifact .artifacts/state-law/inventory-reachability.json`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Unit | Inventory contains exactly 16 German states and one outcome per state. | Validation passes complete inventory and rejects duplicates/missing states. |
| Unit | Inventory rejects unknown state codes and malformed state-law IDs. | Only the fixed German state set is accepted. |
| Unit | `derive_state_law_id` enforces `state:<state-code>/<stable-law-slug>` and rejects mismatched stored IDs. | Phase 9 receives stable IDs without reinterpreting inventory. |
| Unit | Adapter class and source limitation records are valid. | Every state maps to Phase 9, Phase 10, or limitation-only handling. |
| Unit | Limitation-only records reference real Phase 1-compatible limitation records. | Dangling or incomplete limitation IDs fail. |
| Gate | Reachability artifact records status/content type/hash for non-limitation official sources. | Phase 8 has persisted source availability evidence outside default CI. |
| Negative | Missing official URL/provenance or invalid state code fails validation. | Errors identify the state record. |

### Test Integrity Constraints

- Do not add state-law records to `mcp/tests/fixtures/normalized/` in this phase.
- Do not weaken source limitation validation for incomplete state inventory records.
- Live reachability checks must stay outside default `scripts/verify_release.py`.

## Rollback Strategy

Remove state-law inventory code/data/tests/script and docs notes. No runtime serving behavior should be affected because parsers are not implemented in this phase.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Inventory record location | Python constants; JSON data file | JSON data file | The inventory is data that later phases and gates can consume without importing code. |
| Unstable official source handling | Leave pending; limitation-only | Limitation-only | Every state needs an explicit outcome before parser work begins. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/sources.py` | `GERMAN_SOURCES`, `SOURCE_SPECS` | Current sources cover federal GII and DSGVO only, not states. |
| `mcp/legal_texts/validation.py` | `_validate_source` | Current source metadata validation does not know state jurisdiction/source format. |
| `docs/features/supported-laws.md` | Current canonical IDs table | No state-law IDs or jurisdiction encoding exist today. |

### Mismatches / Notes

- There is no state-law source family in current runtime or docs.
- Phase 8 inventory should not create parser claims; imported records start in Phase 9 or Phase 10.
