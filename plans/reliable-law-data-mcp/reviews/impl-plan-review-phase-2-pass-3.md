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

The corrected Phase 2 implementation plan is concrete, scoped, and executable without material guessing. It now uses the German DSGVO Cellar expression `0004.02`, the Publications Office URL `https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_1`, language `DE`, and `<LG.DOC>DE</LG.DOC>` validation, while explicitly rejecting the Dutch `0017.02` expression for German fixtures. I found no remaining functional, technical, or actionability findings.

## Scope Alignment

Phase 2 scope is correctly represented. The plan covers reproducible `gesetze-im-internet.de` imports for German laws, DSGVO Cellar probing as a separate `eur-lex-cellar` source kind, raw snapshot storage, hashes, manifests, manifest comparison, controlled import failures, invalid-path regression probes, and source documentation.

The plan avoids scope creep. It explicitly keeps runtime parser, MCP serving, Docker migration, normalization, resolver, search, and HTTP work out of Phase 2 except as code/documentation anchors.

## Technical Feasibility

The proposed new modules under `mcp/legal_texts/` are isolated from the current legacy runtime path and fit the repository's existing Python structure. The plan's standard-library JSON-compatible records, `urllib.request` with injectable fetcher, deterministic fixture tests, and opt-in live probe command are feasible.

The DSGVO correction is internally consistent across `source-matrix.md`, `contracts.md`, `plan.md`, and `implementation/phase-2-impl.md`. A live sanity check of the corrected Cellar URL returned HTTP 200, content type `application/xml;type=fmx4;charset=UTF-8`, and `<LG.DOC>DE</LG.DOC>`.

## Prior Finding Verification

| Prior Finding | Status | Verification |
| ------------- | ------ | ------------ |
| Live source verification path | Fixed | Step 3 and the testing plan require `PYTHONPATH=mcp python3 -m legal_texts.importer --probe-live`, with expected output for 18 German importable probes, the DSGVO XML probe, and two invalid-path 404 probes. |
| DSGVO CELEX/Cellar/expression/language metadata | Fixed | The plan now requires CELEX `32016R0679`, Cellar work `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`, expression `0004.02`, language `DE`, XML content type, `<LG.DOC>DE</LG.DOC>`, source URL, content hash, and byte size. |
| Reject Dutch DSGVO expression | Fixed | `source-matrix.md` states that `0017.02` is Dutch (`NL`) and must not be used for German fixtures; the Phase 2 testing plan requires rejection of Dutch `0017.02` for German fixtures. |
| Documentation deliverable | Fixed | Step 8 updates `docs/features/data-preparation.md`, `docs/modules/data-preparation.md`, and optionally `docs/overview.md` for supported sources, invalid paths, DSGVO provenance, manifest fields, local snapshot directories, and the legacy runtime boundary. |
| Independent source-matrix oracle | Fixed | Step 7 requires `mcp/tests/fixtures/source_matrix_expected.json` as an independent oracle listing all nine German laws, DSGVO, valid URLs, and `tddsg`/`pangv` expected 404 probes. |
| Manifest identity | Fixed | The Phase 2 model clarifications set `ManifestRecord.dataset_id` and `ManifestRecord.snapshot_id` to the raw snapshot directory name for Phase 2 manifests. |
| Importer-only no-Bundestag guard | Fixed | Step 7 scopes the source-independence test to `mcp/legal_texts/sources.py` and `mcp/legal_texts/importer.py`, avoiding false failures from legacy runtime files. |
| `stand_date_status` serialized shape | Fixed | The model clarifications require `stand_date`, `stand_date_status`, and `stand_date_issue` on every `SourceMetadata` object, with allowed statuses `present`, `not_exposed`, and `known_issue`. |

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

The Required Context list is sufficient. It includes the plan, Phase 2 scope, contracts, source matrix, prior Phase 1 implementation plan, current docs, legacy data-preparation/runtime anchors, existing tests, and Docker boundary. I found no missing context that creates an implementation risk.

## Testing Plan Assessment

### Test Integrity Check

The plan preserves existing parser and library tests, keeps new import tests network-free by default, and requires the new import layer not to depend on `bundestag/gesetze`. Existing legacy references are treated as deferred runtime migration work rather than false Phase 2 failures.

### Test Gaps

No real test gaps found.

### Real-World Testing

Real-world testing is explicitly planned through the required opt-in live source verification command:

```bash
PYTHONPATH=mcp python3 -m legal_texts.importer --probe-live
```

The expected output is specific enough for completion: 18 importable German index/XML ZIP probes, the DSGVO Cellar XML probe with XML content type and `<LG.DOC>DE</LG.DOC>`, and two passing invalid-path regression probes for `tddsg` and `pangv` expected 404 responses.

## Reality Check Validation

The Reality Check is accurate against the current repository anchors. `prepare_data/prepare_gesetze_im_internet.sh` still uses `bundestag/gesetze-tools`, `mcp/parser.py` still has the legacy Bundestag Markdown loader and `index.md` folder loader, `mcp/config.py` still defaults to `/app/gesetze/`, and `Dockerfile` still clones `bundestag/gesetze`. The plan correctly adds the Phase 2 importer alongside those paths and defers runtime migration to later phases.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | Proceed with Phase 2 execution. |

## Recommendations

1. Proceed with Phase 2 execution.
2. Keep the live source probe as a completion gate outside the default pytest command, as planned.
