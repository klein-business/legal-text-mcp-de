---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 4
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 4 - GII bulk normalization and coverage gates

> Reviewing implementation of [Phase 4](../phases/phase-4.md)
> Against [Implementation Plan](../implementation/phase-4-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Rework

The fixture-backed bulk normalization path, terminal-state manifest/package writing, generated package validation, TDDDG canonical ID mapping, and fast release verification are mostly in place. However, the critical-law gate can pass when BDSG/TDDDG payloads are merely absent from the local payload directory, and the required parser-variant matrix/structural fixture coverage is only represented by a placeholder. These are Phase 4 gate-quality issues and should be corrected before accepting the phase.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | All parseable fixture GII ZIPs produce validated law and norm records. | Mostly | `run_gii_bulk_normalization` imports fixture ZIPs and `test_bulk_normalization_assigns_terminal_states_and_validates_generated_package` validates laws/norms/package; release verification passed 116 tests. | The article-container fixture is reduced to only its child paragraph because container records are filtered out, so structural coverage is incomplete. |
| 2 | Parse failures are recorded in the manifest instead of silently omitted. | Yes | `parsefail.zip` becomes `parse_failed` in manifest/source limitations; covered by `test_source_limitations_represent_failures_without_fake_laws`. | None for the covered fixture path. |
| 3 | Full-discovery coverage gate proves every discovered GII source has exactly one terminal state. | Mostly | `verify_gii_corpus_gate.py` produces `gii-corpus-gate.v1`; `.artifacts/gii-corpus/gate.json` shows 7 discovered sources and 7 terminal states. | The gate is local/fixture evidence only, which is acceptable for this review scope; no live full-corpus import was required. |
| 4 | BDSG and TDDDG generated records resolve from the normalized package with GII provenance, unless a release-blocking source limitation is recorded. | Partial | Imported fixture path resolves `TDDDG` to `tdddg` with upstream `ttdsg` provenance and `BDSG` to `bdsg_2018`. | Missing local payloads are automatically converted into release-blocking upstream limitations, so the exception can pass without official upstream evidence. |
| 5 | Sampled parser checks are used only for parser regression coverage, not as proof of full corpus completeness. | Mostly | Docs describe GII corpus gates as explicit local/full-corpus gates and not ordinary release verification. | The parser-variant matrix is a string placeholder rather than a documented fixture matrix, so the sampled coverage boundary is under-specified. |
| 6 | Generated full corpus data remains excluded from Git. | Yes | `.gitignore` ignores `.artifacts/`; `git check-ignore -v .artifacts/gii-corpus/gate.json` confirms the local evidence is ignored. | None. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Bulk GII normalization over discovery records with terminal manifest states. | Implemented in `mcp/legal_texts/gii_bulk.py` using explicit local payloads and generated package output. | Yes, no downloader path in this phase. | Acceptable for this fixture/local review scope. |
| 2 | Representative parser variants plus parser-variant matrix for paragraphs, article children, annexes, sections, containers, repealed/empty, and title-only cases. | Existing paragraph and article-child fixtures remain; bulk gate reports `{"gii_xml": "fixture-v1"}` only. | Yes. | Finding 2. |
| 3 | Stable canonical IDs and provenance, preserving existing aliases. | `SOURCE_SPECS` maps `ttdsg` to `tdddg`; tests cover `TDDDG`, `BDSG`, and source path provenance. | Minor. | Canonical/source-path behavior is correct; display fields are less polished but not phase-blocking. |
| 4 | Terminal-state and critical-law gates. | Terminal-state gate is implemented and validates the fixture package. | Yes. | Finding 1: critical-law source-unavailable exception is too permissive. |

## Code Quality Assessment

### Findings

- **Major**: Critical-law `source_unavailable` is generated from local fixture absence, not upstream evidence. In `mcp/legal_texts/gii_bulk.py:176-197`, any missing local ZIP becomes `source_unavailable` with `release_blocking=True`; `mcp/legal_texts/gii_bulk.py:306-310` then marks every `source_unavailable` as `official_upstream_evidence`; `mcp/legal_texts/gii_bulk.py:116-117` accepts that as satisfying the BDSG/TDDDG critical-law exception. This conflates "operator did not provide a local payload" with "official upstream source is unavailable."
- **Major**: Parser-variant coverage is incomplete relative to Phase 4 scope. The implementation plan requires a fixture-backed matrix covering structural variants, but `mcp/legal_texts/gii_bulk.py:158-160` only emits a placeholder version string, and `mcp/legal_texts/gii_bulk.py:211-215` strips empty container records instead of validating them as generated `container` units.

## Testing Assessment

### Verify Command Result

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: Passed: 116 pytest tests passed; HTTP CLI E2E OK; MCP streamable HTTP E2E OK.

### Additional Review Checks

- Inspected `.artifacts/gii-corpus/gate.json`; it reports 7 discovered fixture sources, 4 imported sources, 3 source limitations, and no validation errors.
- Ran a throwaway negative gate with the same discovery fixture and an empty payload directory. It exited 0 with `imported_sources=0` while reporting both BDSG and TDDDG as release-blocking `source_unavailable`, confirming Finding 1.

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `mcp/tests/test_gii_bulk_normalization.py` | Terminal states, generated package validation, critical-law happy/error paths, canonical ID/provenance. | Mostly | It codifies the too-permissive BDSG missing-payload exception in `test_critical_law_gate_allows_release_blocking_upstream_unavailable`. |
| `mcp/tests/test_normalizer_gii.py` | Existing paragraph and article-child parser behavior. | Partially | It does not cover the Phase 4 parser matrix variants: annex, section, generated `container`, repealed/empty, or title-only records. |
| Release gate | Fast fixture test suite plus local HTTP/MCP E2E. | Yes | Live/full corpus import is intentionally not part of this phase review. |

### Real-World Testing

Performed local fixture-gate and release verification only. Live full-corpus import was not performed and is not required by this review scope; the remaining risk is that fixture payload handling currently allows a false critical-law pass when required local payloads are absent.

## Scope Compliance

### Findings

- No Phase 5+ DSGVO/EU/state-law work is required or missing for this review.
- Generated corpus evidence is local under `.artifacts/` and ignored by Git.
- The implementation stayed within the MCP/server, scripts, tests, docs, and plan artifact surface expected for Phase 4.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were deleted.
- [x] No existing tests were disabled.
- [x] No existing assertions were weakened in tracked diffs reviewed.
- [x] All pre-existing tests in the configured release gate still pass.

### Findings

- The main regression risk is false-positive gate evidence rather than runtime breakage: a critical law can disappear from the generated package while the gate still exits successfully if the local payload is missing.

## Documentation & Cleanup

### Findings

- `docs/features/law-loading-and-indexing.md:52` says container norms such as `egbgb/art:246a` carry child references, but the Phase 4 bulk package filters the empty article container out. Align the implementation, the docs, and the parser-variant matrix.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Critical-law gate | Missing local BDSG/TDDDG payloads are accepted as release-blocking upstream unavailability, so the gate can pass with no critical laws imported and no official upstream evidence. | Separate local payload absence from official upstream unavailability. For BDSG/TDDDG, fail missing local payloads unless an explicit upstream-source limitation artifact with real fetch/probe evidence is provided. |
| 2 | Major | Parser coverage | Phase 4's parser-variant matrix and structural variant coverage are incomplete; the gate emits a placeholder and bulk normalization drops container records. | Add the documented matrix fixture/file and tests for required variants; map structural containers to generated `unit="container"` records instead of filtering them out. |

## Recommendations

1. Blocking: tighten the critical-law exception so only imported/resolvable records or explicit upstream-source evidence can satisfy BDSG/TDDDG.
2. Blocking: add the parser-variant matrix and structural tests required by the Phase 4 implementation plan, including generated container behavior.
3. Follow-up: preserve curated display metadata (`BDSG`, `TDDDG`, display names) for generated laws where `SOURCE_SPECS` has an existing entry.
