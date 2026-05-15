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

**Verdict**: Needs Rework

The implementation is directionally correct and keeps the manifest contract outside runtime loading, but two contract holes allow manifests that the Phase 1 plan explicitly meant to reject. In addition, the planned source-provenance documentation note was not implemented. The release gate passes, but acceptance should wait until the manifest contract rejects third-party legal-text IDs and incomplete source limitation records.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Existing fixture dataset still loads and passes release gates. | Yes | `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` passed: 62 pytest tests, HTTP CLI E2E OK, MCP streamable HTTP E2E OK. | None. |
| 2 | Manifest validation rejects missing source IDs, missing terminal states, duplicate discovered-source records, and unprovenanced exclusions. | Partial | `mcp/tests/test_corpus_manifest.py`; `mcp/legal_texts/manifest.py` rejects duplicate discovered sources, terminal missing in terminal mode, and incomplete policy exclusions. | `source_limitations` can omit `terminal_state` when the manifest is in discovery mode, so limitation records can avoid the terminal-state taxonomy. |
| 3 | Manifest validation rejects source records missing required provenance for their source family. | Mostly | `_validate_source_family_provenance()` dispatches to GII, EUR-Lex/Cellar, state-law, and third-party-scope checks; valid fixture covers all source families. | Test coverage is thinner than planned for missing family-specific provenance, but the main blocker is the source-limitation terminal-state gap above. |
| 4 | Canonical ID rules cover generated GII laws, EUR-Lex acts, state-law records, third-party relationship records, and new citation units. | Partial | `_validate_canonical_ids()` rejects duplicate IDs, CELEX/source mismatches, and invalid state-law prefixes; `_validate_relationship_sources()` rejects law-ID fields inside relationship-source records. | `canonical_ids` accepts `source_family="third-party-scope"`, allowing a third-party scope source to define a legal-text canonical ID outside `relationship_sources`. |
| 5 | Every later source family can reference this phase's contract without defining its own incompatible manifest shape. | Partial | `mcp/legal_texts/manifest.py` establishes shared source-family, terminal-state, provenance, relationship-source, and generated-package sections. | The two accepted invalid shapes above would force later phases either to special-case them or harden the contract later. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Introduce corpus manifest model with shared source families, terminal states, provenance, envelope, generated-package, relationship-source, and source-limitation sections. | Added `mcp/legal_texts/manifest.py` with constants, schema version, envelope fields, generated-package reservation, and validation helpers. | Minor | Correct boundary and vocabulary, but source-limitations are not always terminal records. |
| 2 | Add manifest validation rules, including terminal coverage and source-family provenance. | Added validation entry point and data-driven helper checks. | Yes | Validation mode handling works for discovered sources but is too permissive for `source_limitations`. |
| 3 | Define canonical ID and alias policy checks. | Added duplicate ID, CELEX, state-law prefix, alias migration, and relationship-source law-ID checks. | Yes | The third-party canonical-ID prohibition is incomplete because the check is only applied to `relationship_sources`. |
| 4 | Add representative manifest fixtures. | Added eight manifest fixtures under `mcp/tests/fixtures/manifest/`; `.gitignore` exceptions make them addable. | No | Fixture tracking is correct; `git add -n mcp/tests/fixtures/manifest/*.json` reports all fixture files as addable. |
| 5 | Add contract tests and documentation note. | Added `mcp/tests/test_corpus_manifest.py` and included it in `scripts/verify_release.py`. | Yes | `docs/features/source-provenance.md` has no manifest-contract note or terminal-state list update. |

## Code Quality Assessment

### Findings

- **Major**: `mcp/legal_texts/manifest.py:96` and `mcp/legal_texts/manifest.py:314` validate `canonical_ids` without rejecting `source_family="third-party-scope"`. A manifest with `{"canonical_id": "fake-third-party-law", "source_family": "third-party-scope", ...}` returns no errors, which violates the plan's rule that third-party scope data must not create legal-text law IDs.
- **Major**: `mcp/legal_texts/manifest.py:100` passes the manifest-wide terminal requirement into `_validate_source_limitations()`, and `mcp/legal_texts/manifest.py:189` therefore allows discovery-mode source limitations without `terminal_state`. Source limitations are terminal failure/limitation records by contract, so this permits an incompatible limitation schema.
- **Minor**: The implementation plan required a concise source-provenance documentation note and terminal-state list, but `docs/features/source-provenance.md` remains unchanged.

## Testing Assessment

### Verify Command Result

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: Passed; 62 pytest tests passed, HTTP CLI E2E OK, MCP streamable HTTP E2E OK.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_corpus_manifest.py` | Valid terminal and discovery fixtures, validation-mode conflicts, missing envelope fields, duplicate sources, terminal-state field requirements, canonical policy checks, relationship law-ID rejection, source-limitation reuse. | Yes | Does not include regression cases for third-party entries in `canonical_ids` or discovery-mode `source_limitations` missing terminal state. |
| `mcp/tests/test_dataset_validation.py` through release gate | Confirms existing normalized fixture package validation remains intact. | Yes | None. |
| HTTP and MCP E2E via release gate | Confirms current runtime behavior remains compatible. | Yes | Runtime does not consume the new manifest yet, by Phase 1 design. |

### Real-World Testing

Not performed, and acceptable for this phase. Phase 1 is a fixture-backed schema and validation foundation; live discovery/import checks are explicitly deferred to later phases. The release gate and focused manifest tests are the appropriate evidence for this implementation, but they need the missing negative cases above.

## Scope Compliance

### Findings

- No out-of-scope runtime wiring was introduced. `NormalizedDataset` and existing normalized fixtures were not changed, and the release gate remains fixture-backed with `SKIP_LIVE_SOURCE_MATRIX=true`.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened.
- [x] All pre-existing release-gate tests still pass.

### Findings

- The primary regression risk is forward-looking: later phases may build on accepted invalid manifest shapes unless the two contract gaps are closed before proceeding.

## Documentation & Cleanup

### Findings

- **Minor**: `docs/features/source-provenance.md` does not document the new corpus manifest as the completeness contract or list the terminal states, despite Phase 1 deliverables and implementation Step 5 requiring that note.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Canonical ID policy | `canonical_ids` accepts `third-party-scope` sources as legal-text canonical IDs. | Reject `third-party-scope` entries in `canonical_ids` or otherwise require relationship-only IDs that cannot become law IDs; add a negative fixture/test. |
| 2 | Major | Source limitations | `source_limitations` can omit `terminal_state` in discovery mode. | Validate source limitations with terminal states required regardless of manifest validation mode; add a discovery-mode negative test. |
| 3 | Minor | Documentation | The source-provenance manifest-contract note was not added. | Update `docs/features/source-provenance.md` with the manifest role, source families, and terminal-state list. |

## Recommendations

1. Block acceptance until the two Major manifest-validation gaps are fixed and covered by tests.
2. Complete the planned source-provenance documentation note before closing Phase 1.
3. After fixes, rerun `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_corpus_manifest.py mcp/tests/test_dataset_validation.py` and the full `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` gate.
