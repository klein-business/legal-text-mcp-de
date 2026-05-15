---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 1
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 1 - Manifest and corpus contract foundation

> Reviewing implementation of [Phase 1](../phases/phase-1.md)
> Against [Implementation Plan](../implementation/phase-1-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Accepted

The Phase 1 implementation now satisfies the manifest-contract scope and the prior review findings are resolved. The validator rejects third-party scope entries in `canonical_ids`, source limitations require terminal states regardless of manifest validation mode, the new negative fixtures cover both regressions, and the source-provenance documentation now describes the corpus manifest contract, source families, and terminal states.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing fixture dataset still loads and passes release gates. | Yes | `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` passed: 64 pytest tests, HTTP CLI E2E OK, MCP streamable HTTP E2E OK. | None. |
| 2 | Manifest validation rejects missing source IDs, missing terminal states, duplicate discovered-source records, and unprovenanced exclusions. | Yes | `mcp/legal_texts/manifest.py` validates source IDs, duplicate source keys, terminal states, and policy-exclusion fields; `mcp/tests/test_corpus_manifest.py` covers missing envelope data, duplicate sources, terminal-state requirements, and copied-text policy exclusions. | None. |
| 3 | Manifest validation rejects source records missing required provenance for their source family. | Yes | `_validate_source_family_provenance()` dispatches GII, EUR-Lex/Cellar, state-law, and third-party-scope checks; negative fixture coverage includes missing state-law provenance in discovered sources and source limitations. | None. |
| 4 | Canonical ID rules cover generated GII laws, EUR-Lex acts, state-law records, third-party relationship records, and new citation units. | Yes | `_validate_canonical_ids()` rejects duplicates, CELEX/source mismatches, state-law prefix violations, missing state codes, and `third-party-scope` legal-text canonical IDs; `_validate_relationship_sources()` rejects law-ID fields in relationship-source records. | None. |
| 5 | Every later source family can reference this phase's contract without defining its own incompatible manifest shape. | Yes | `mcp/legal_texts/manifest.py` defines shared source families, terminal states, provenance validation, canonical-ID policy, relationship-source records, generated-package metadata, alias migrations, and terminal source limitations. | None. |

## Prior Review Resolution

| Prior Finding | Resolution Evidence | Status |
| ------------- | ------------------- | ------ |
| Major: `canonical_ids` accepted `third-party-scope` sources as legal-text IDs. | `mcp/legal_texts/manifest.py` rejects `source_family == "third-party-scope"` in canonical ID records; `invalid_third_party_canonical_id.json` and `test_canonical_ids_reject_third_party_scope_sources` cover the case. | Resolved. |
| Major: `source_limitations` could omit `terminal_state` in discovery mode. | `_validate_source_limitations()` now calls `_validate_terminal_state(..., True)` unconditionally; `invalid_discovery_source_limitation_missing_terminal.json` and `test_source_limitations_require_terminal_state_in_discovery_mode` cover the case. | Resolved. |
| Minor: source-provenance docs did not describe the manifest contract. | `docs/features/source-provenance.md` now documents `corpus-manifest.v1`, the four source families, the five terminal states, and third-party relationship-source constraints. | Resolved. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Introduce the corpus manifest model. | Added `mcp/legal_texts/manifest.py` with schema/version constants, source families, terminal states, envelope checks, relationship sources, generated-package metadata, alias migrations, and source limitations. | No | In scope. |
| 2 | Add manifest validation rules. | Added validation for envelope fields, validation mode conflicts, duplicate source records, terminal states, terminal-state-specific fields, source-family provenance, source limitations, and generated-package metadata. | No | In scope. |
| 3 | Define canonical ID and alias policy checks. | Added canonical ID duplicate checks, CELEX matching, state-law prefix checks, third-party canonical-ID rejection, relationship-source law-ID rejection, and alias migration validation. | No | In scope. |
| 4 | Add representative manifest fixtures. | Added valid terminal/discovery fixtures plus focused invalid fixtures for envelope, duplicate sources, terminal fields, canonical policy, relationship law IDs, source limitations, discovery-mode limitation terminal states, and third-party canonical IDs. | No | In scope. |
| 5 | Add contract tests and documentation note. | Added `mcp/tests/test_corpus_manifest.py`, included it in `scripts/verify_release.py`, and updated `docs/features/source-provenance.md`. | No | In scope. |

## Code Quality Assessment

The implementation is scoped to the Phase 1 contract and preserves runtime behavior by keeping the new manifest validator out of `NormalizedDataset` loading. The validator follows the existing lightweight validation style, returns actionable string errors, uses table-like constants for vocabularies and required fields, and introduces no new dependencies or silent fallbacks.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_corpus_manifest.py mcp/tests/test_dataset_validation.py`
- **Exit Code**: 0
- **Result**: Passed; 15 tests passed.

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: Passed; 64 pytest tests passed, HTTP CLI E2E OK, MCP streamable HTTP E2E OK.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_corpus_manifest.py` | Positive and negative manifest contract behavior, including the two prior Major regressions. | Yes | None. |
| `mcp/tests/test_dataset_validation.py` through focused and release gates | Confirms existing normalized fixture validation remains intact. | Yes | None. |
| HTTP and MCP E2E through release gate | Confirms Phase 1 did not regress existing serving behavior. | Yes | None. |

### Real-World Testing

Not performed, which is acceptable for this phase. Phase 1 is a fixture-backed manifest schema and validation foundation; live discovery, import, and full-corpus validation gates are explicitly deferred to later phases. The fixture-backed release gate is the appropriate Phase 1 evidence.

## Scope Compliance

The implementation stayed within Phase 1. It introduced the contract, fixtures, tests, release-gate inclusion, and documentation without wiring the manifest into runtime package loading or attempting deferred GII, EUR-Lex, state-law, or relationship imports.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened.
- [x] All pre-existing release-gate tests still pass.

Existing runtime risk is low because the new manifest code is directly tested but not yet part of serving startup. Forward risk is acceptable because the contract now rejects the invalid shapes identified in the prior review.

## Findings Summary

| Severity | Count |
| -------- | ----- |
| Critical | 0 |
| Major | 0 |
| Minor | 0 |
| Note | 0 |

No Critical, Major, Minor, or Note findings.

## Recommendations

1. Accept Phase 1 and proceed to the next planned phase.
