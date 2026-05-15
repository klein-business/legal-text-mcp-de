---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 12
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 12 - Scaling, search, and operational corpus gates

> Implements [Phase 12](../phases/phase-12.md) of [full-privacy-corpus](../plan.md)

## Approach

Add fixture-backed performance tests and opt-in operational gates that validate full generated corpus import, `package.json` metadata, package loading, search, coverage artifacts, and release evidence without making PR CI download or import the full internet corpus. Record benchmark thresholds and migration decisions when JSON/package/search budgets are missed.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Add benchmark helpers, corpus gate scripts, artifact validation, dataset exclusion checks, and search/runtime scale tests. |
| [container-runtime](../../../docs/modules/container-runtime.md) | modify | Document or validate external generated dataset mounting if gate scripts need it. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-12.md` | Gated scaling thresholds and validation bundle requirements. |
| `plans/full-privacy-corpus/implementation/phase-4-impl.md` | GII bulk import and terminal-state artifact inputs. |
| `plans/full-privacy-corpus/implementation/phase-5-impl.md` | DSGVO full-count/version/hash gate inputs. |
| `plans/full-privacy-corpus/implementation/phase-7-impl.md` | EU neighbor imported-or-limited evidence. |
| `plans/full-privacy-corpus/implementation/phase-10-impl.md` | State-law 16-outcome evidence. |
| `plans/full-privacy-corpus/implementation/phase-11-impl.md` | Runtime coverage APIs and generated package loading behavior. |
| `mcp/legal_texts/dataset.py` | Package loading and in-memory indexes to benchmark. |
| `mcp/legal_texts/search.py` | Search indexing and query behavior to benchmark. |
| `mcp/legal_texts/runtime.py` | Serving readiness and runtime composition. |
| `scripts/verify_release.py` | Existing fast release gate that must remain fixture-backed. |
| `.gitignore` | Generated production corpus exclusion rules. |
| `mcp/tests/test_search.py` | Current deterministic search expectations. |

## Implementation Steps

### Step 1: Add benchmark fixture/generator helpers

- **What**: Add deterministic fixture generation for larger local packages or a benchmark harness that can point at a generated package path.
- **Where**: New `scripts/benchmark_corpus_runtime.py`; tests under `mcp/tests/test_search_scaling.py`.
- **Why**: Runtime load, memory, and search budgets need repeatable local evidence.
- **Thresholds**: The benchmark output must record documented environment fields, load time, sampled search p95, memory estimate, package size, record counts, and whether each Phase 12 threshold passed or requires a migration decision.
- **Considerations**: Keep generated benchmark data outside Git; commit only tiny generator fixtures/config.

### Step 2: Add opt-in full-corpus gate scripts

- **What**: Add or compose scripts for full GII terminal-state coverage, DSGVO count/version/hash evidence, BDSG/TDDDG resolution evidence, EU neighbor imported-or-limited states, all 16 state-law outcomes, and relationship graph discovered-or-limited validation.
- **Where**: New `scripts/verify_full_corpus_bundle.py` plus scripts from earlier phases such as `verify_gii_corpus_gate.py`.
- **Why**: Acceptance requires persisted full-corpus validation evidence bundle.
- **Bundle schema**: `verify_full_corpus_bundle.py` must write `schema_version="full-corpus-validation-bundle.v1"`, artifact paths/hashes for GII, DSGVO, EU neighbors, state law, relationships, runtime readiness, benchmark summary, and migration decisions. Each section must include `status`, `generated_at`, `source_artifact`, and `errors`.
- **Considerations**: These scripts must be explicit/scheduled and not called by default `scripts/verify_release.py`.

### Step 3: Validate dataset exclusion and artifact handling

- **What**: Ensure `.gitignore` excludes generated production data paths such as `data/sources/raw/`, `data/normalized/`, and full-corpus artifacts while allowing small committed fixtures.
- **Where**: `.gitignore`; `mcp/tests/test_operational_corpus_gates.py`.
- **Why**: Full generated datasets must remain outside Git.
- **Considerations**: Do not ignore committed fixture directories under `mcp/tests/fixtures/`.

### Step 4: Add package-format/search migration decision records

- **What**: Add a decision record template or generated artifact section that records whether JSON remains sufficient or whether sharded JSONL/SQLite/search-index migration is required if thresholds are missed.
- **Where**: `docs/operations/full-corpus-gates.md` or generated bundle metadata; tests validate required fields.
- **Why**: Phase 12 acceptance allows threshold misses only with a documented migration decision.
- **Considerations**: Do not implement SQLite or search backend migration unless the phase execution evidence requires it and scope remains acceptable.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_operational_corpus_gates.py mcp/tests/test_search_scaling.py mcp/tests/test_runtime_coverage_relationships.py`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Unit | Validation bundle schema requires all full-corpus evidence sections. | Missing evidence fails with explicit errors. |
| Scale fixture | Larger fixture package loads and sampled search remains deterministic. | Runtime/search tests pass within local fixture budget. |
| Benchmark | Threshold pass/fail and migration decision fields are required. | Missed budgets cannot be ignored silently. |
| Git hygiene | Generated production data paths are ignored while fixtures are tracked. | Exclusion tests pass. |

### Test Integrity Constraints

- Do not add full-corpus network scripts to `scripts/verify_release.py`.
- Do not commit generated production package artifacts to satisfy tests.
- Do not relax search correctness ordering from `mcp/tests/test_search.py` for performance.

## Rollback Strategy

Remove benchmark/gate scripts, operational tests, exclusion changes, and decision-record docs. Runtime code from Phase 11 remains functional without operational full-corpus gates.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Package migration if budgets fail | Keep JSON; sharded JSONL; SQLite | Defer to benchmark evidence | Phase 12 records a decision only when thresholds are measured. |
| Full-corpus gates in PR CI | Default PR gate; explicit/scheduled only | Explicit/scheduled only | The plan requires fast CI to remain fixture-backed. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/dataset.py` | `NormalizedDataset.__init__` | Current loader reads full JSON files into memory. |
| `mcp/legal_texts/search.py` | `SearchService.__init__`, `search_laws` | Current search builds in-memory rows and scans them. |
| `scripts/verify_release.py` | `main`, `selected_tests` | Default release gate is fixture-backed plus local E2E. |
| `docs/features/source-provenance.md` | Raw/normalized data separation | Generated raw/normalized data paths are already documented as local/ignored. |

### Mismatches / Notes

- Current runtime has no benchmark instrumentation or memory measurement.
- Current search is linear in text-bearing norms, so full-corpus budgets may require a migration decision after measurement.
