---
type: review
entity: implementation-plan-review
plan: "reliable-law-data-mcp"
phase: 2
status: final
reviewer: "general"
created: "2026-05-14"
---

# Implementation Plan Review: Phase 2 - Reproducible Source Import

> Reviewing [Phase 2 Implementation Plan](../implementation/phase-2-impl.md)
> Against [Phase 2 Scope](../phases/phase-2.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Ready

The revised implementation plan is concrete enough to execute without guessing. It stays within Phase 2 by adding a reproducible importer, source specs, manifest records, validation tests, and documentation while explicitly leaving runtime dataset migration, MCP contract changes, normalization, resolver, search, and HTTP work to later phases. I found no remaining functional, technical, or actionability findings that should block execution.

## Scope Alignment

Phase 2 scope is correctly represented. The plan covers German `gesetze-im-internet.de` source probing, DSGVO Cellar probing, raw snapshot storage, hashes, manifests, manifest comparison, source-kind separation, controlled import failures, and supported-source documentation.

It also avoids scope creep. Existing Markdown parser/runtime behavior remains unchanged until later phases, and the plan explicitly does not switch Docker or MCP serving to the new dataset in Phase 2.

## Technical Feasibility

The proposed module split is feasible for the current codebase. `mcp/legal_texts/importer.py`, `sources.py`, `models.py`, and `errors.py` are new, isolated modules, so they can be introduced without destabilizing `mcp/parser.py`, `mcp/server.py`, or the existing parser/library tests.

The plan's use of standard-library serialization and `urllib.request` with an injectable fetcher fits the repository's current dependency profile. The raw snapshot and manifest model aligns with `contracts.md`, and the fixture-backed tests keep CI deterministic while preserving a required opt-in live verification path.

## Prior Finding Verification

| Prior Finding | Status | Verification |
| ------------- | ------ | ------------ |
| Live source verification path | Fixed | Step 3 adds `PYTHONPATH=mcp python3 -m legal_texts.importer --probe-live`; the testing plan marks it required before Phase 2 completion and defines expected 18 German 200 checks, DSGVO XML content-type check, and two invalid-path 404 checks. |
| DSGVO CELEX/Cellar/expression/language metadata | Fixed | Phase 2 model clarifications and Step 4 require CELEX `32016R0679`, Cellar work `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`, expression `0017.02`, language `DE`, XML content type, source URL, content hash, and byte size. |
| Documentation deliverable | Fixed | Step 8 updates `docs/features/data-preparation.md`, `docs/modules/data-preparation.md`, and optionally `docs/overview.md`, covering supported sources, invalid paths, DSGVO Cellar provenance, manifest fields, local snapshot directories, and the legacy runtime boundary. |
| Independent source-matrix oracle | Fixed | The affected modules and Step 7 add `mcp/tests/fixtures/source_matrix_expected.json` as an independent expected source table, explicitly listing all nine German laws, DSGVO, valid URLs, and `tddsg`/`pangv` expected 404 probes. |
| Manifest identity | Fixed | The Phase 2 model clarification states that `ManifestRecord.dataset_id` and `ManifestRecord.snapshot_id` both equal the raw snapshot directory name for manifests under `data/sources/raw/{snapshot_id}/manifest.json`. |
| Importer-only no-Bundestag guard | Fixed | Step 7 adds a focused source-independence test scoped to `mcp/legal_texts/sources.py` and `mcp/legal_texts/importer.py`, avoiding false failures from legacy runtime files that still legitimately reference `bundestag/gesetze`. |
| `stand_date_status` serialized shape | Fixed | The Phase 2 model clarification requires every `SourceMetadata` object to include `stand_date`, `stand_date_status`, and `stand_date_issue`, with allowed statuses `present`, `not_exposed`, and `known_issue`; Step 6 requires manifests to preserve that shape. |

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add Shared Import Records and Errors | Yes | Yes | None. |
| 2 | Encode Source Specifications From the Matrix | Yes | Yes | None. |
| 3 | Implement Source Probing | Yes | Yes | None. |
| 4 | Validate DSGVO Cellar Metadata | Yes | Yes | None. |
| 5 | Implement Raw Snapshot Download and Hashing | Yes | Yes | None. |
| 6 | Generate and Compare Manifests | Yes | Yes | None. |
| 7 | Add Fixture-Backed Import Tests | Yes | Yes | None. |
| 8 | Update Source Import Documentation | Yes | Yes | None. |
| 9 | Protect Local Snapshot Directories | Yes | Yes | None. |

## Required Context Assessment

The Required Context list is sufficient for execution. It includes the plan, phase scope, contracts, source matrix, relevant prior implementation plan, current docs, current legacy preparation/runtime anchors, existing tests, and Docker boundary. I found no missing context that creates an implementation risk.

## Testing Plan Assessment

### Test Integrity Check

The test plan preserves existing behavior by requiring `mcp/tests/test_parser.py` and `mcp/tests/test_library.py` to remain behaviorally unchanged unless only path setup changes are needed. It also states that new import tests must not perform live network requests by default and must not weaken the later removal requirement for `bundestag/gesetze`.

### Test Gaps

No blocking gaps found. The primary verify command covers new source-matrix/import tests plus existing parser/library regression tests, and the separate required live command covers real upstream source verification without making default CI network-dependent.

### Real-World Testing

Real-world testing is explicitly planned through the required opt-in live source verification command:

```bash
PYTHONPATH=mcp python3 -m legal_texts.importer --probe-live
```

The expected output is specific enough to verify the phase: all German index/XML ZIP probes, the DSGVO Cellar XML content type, and the two known invalid-path 404 regression probes must be reported as passing before Phase 2 is marked complete.

## Reality Check Validation

The Reality Check is accurate against the current repository. `prepare_data/prepare_gesetze_im_internet.sh` still depends on `bundestag/gesetze-tools`; `mcp/parser.py` still has the legacy Bundestag GitHub Markdown loader and local `index.md` folder loader; `mcp/config.py` defaults to `/app/gesetze/`; and `Dockerfile` still clones `bundestag/gesetze`. The implementation plan correctly treats these as legacy runtime paths deferred to later phases and adds the Phase 2 importer alongside them.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | Proceed with Phase 2 execution. |

## Recommendations

1. Proceed with Phase 2 execution.
2. During implementation, keep the live probe as a required completion gate but outside the default pytest command, as planned.
