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

**Verdict**: Needs Revision

The implementation plan is directionally sound and grounded in the current codebase: it adds a separate import layer, keeps the legacy Markdown runtime unchanged for this phase, and covers source metadata, hashing, invalid-path probes, manifest diffing, and fixture-backed tests. It still needs revision before execution because several phase acceptance criteria are not made concrete enough to verify, especially live source revalidation, DSGVO Cellar metadata validation, documentation deliverables, and an explicit guard that the new import path has no productive dependency on Bundestag demo data.

## Scope Alignment

### Findings

- **Major**: Phase 2 includes documentation for "which laws are safely supported by the current import pipeline" and deliverable-level "Documentation of supported and known-issue source entries" (`phases/phase-2.md:30`, `phases/phase-2.md:53`), but the implementation plan marks `docs/features/data-preparation.md` as "reference only" and has no documentation update step (`implementation/phase-2-impl.md:31`, `implementation/phase-2-impl.md:92`). Add a concrete doc step that updates the relevant feature/module docs or creates a focused provenance/import doc covering supported entries, known invalid paths, DSGVO Cellar handling, and the remaining legacy runtime boundary.

- **Minor**: The plan correctly leaves runtime migration and Docker cleanup to later phases, matching the current `bundestag/gesetze` anchors in `mcp/parser.py:278` and `Dockerfile:6`. However, the Phase 2 acceptance criterion is narrower: the new import path itself must not depend on `bundestag/gesetze` (`phases/phase-2.md:61`). Add an explicit test or review check scoped to `mcp/legal_texts/*` that source specs and importer URLs are only the matrix URLs or injected fixtures, not Bundestag GitHub URLs.

## Technical Feasibility

### Findings

- **Major**: DSGVO Cellar handling is under-specified. The phase requires probing the Publications Office / Cellar XML artifact with status, XML content type, language/expression metadata, and hash (`phases/phase-2.md:25`, `phases/phase-2.md:59`), and the source matrix requires CELEX, Cellar work ID, expression, language, retrieved URL, and content hash to be recorded (`source-matrix.md:37`). The implementation plan only names `eur-lex-cellar`, the Cellar URL, and content-type tests (`implementation/phase-2-impl.md:62`, `implementation/phase-2-impl.md:87`, `implementation/phase-2-impl.md:110`). Add concrete model fields and importer checks for CELEX `32016R0679`, Cellar work `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`, expression `0017.02`, language `DE`, and XML/hash validation.

- **Minor**: Manifest identity is ambiguous. The dataset layout stores raw manifests under `data/sources/raw/{snapshot_id}/manifest.json` (`contracts.md:21`), while `ManifestRecord` requires `dataset_id` (`contracts.md:103`) and the Phase 2 plan writes by `snapshot_id` (`implementation/phase-2-impl.md:73`). Before implementation, specify whether Phase 2's raw manifest uses `snapshot_id` as `dataset_id`, adds a separate `snapshot_id` field, or introduces an import-specific manifest record compatible with later normalized dataset manifests.

- **Minor**: Stand-date metadata is called out, but the representation needs tightening. `SourceMetadata` has `stand_date` and `known_issues` (`contracts.md:55`), while the source matrix requires each snapshot entry to include either `stand_date` or `stand_date_status` and restricts statuses to `present`, `not_exposed`, or `known_issue` (`source-matrix.md:41`). The implementation plan mentions `stand_date_status` but does not say where it lives in the JSON-compatible records (`implementation/phase-2-impl.md:80`). Add the exact serialized shape and validation rule so implementers do not invent incompatible fields.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add Shared Import Records and Errors | Mostly | Mostly | Needs exact DSGVO metadata and stand-date status fields to match contracts and source matrix. |
| 2 | Encode Source Specifications From the Matrix | Yes | Mostly | Good coverage of laws and invalid paths; add a non-self-referential test oracle for matrix coverage. |
| 3 | Implement Source Probing | Mostly | Mostly | Probe mechanics are clear, but live revalidation is left optional despite phase scope requiring it. |
| 4 | Implement Raw Snapshot Download and Hashing | Yes | Yes | Covers raw byte storage, SHA-256, size, URL, and timestamps. |
| 5 | Generate and Compare Manifests | Mostly | Mostly | Covers diffing and ordering; manifest identity and stand-date serialized shape need clarification. |
| 6 | Add Fixture-Backed Import Tests | Mostly | Mostly | Good deterministic CI direction; does not cover live probe revalidation, DSGVO metadata, or importer-only no-Bundestag guard enough. |
| 7 | Protect Local Snapshot Directories | Yes | Yes | Correctly scoped and compatible with committed fixtures. |

## Required Context Assessment

### Missing Context

- `docs/modules/data-preparation.md`: needed because it documents the current `gesetze-tools` workflow and is a likely doc target or contrast point for Phase 2 source-import documentation.
- `docs/modules/container-runtime.md`: useful because the plan explicitly relies on Docker remaining legacy until Phase 7 while ensuring Phase 2 does not reinforce the demo-data dependency.
- `mcp/tests/conftest.py`: needed for an implementer to preserve existing parser/library tests and understand current fixture style.

## Testing Plan Assessment

### Test Integrity Check

The plan identifies existing tests affected by the phase and states that `mcp/tests/test_parser.py` and `mcp/tests/test_library.py` must remain behaviorally unchanged (`implementation/phase-2-impl.md:116`). It also says new import tests must mock network by default and must not weaken the later Bundestag-removal requirement (`implementation/phase-2-impl.md:119`). This satisfies the basic integrity constraint, but the new tests need sharper acceptance hooks as described below.

### Test Gaps

- **Major**: The primary verify command will not prove the phase's live source-probe requirement. Phase 2 includes "Live source probing" for all German matrix entries and DSGVO (`phases/phase-2.md:24`), while the implementation plan chooses mocked tests by default and only mentions a "separate optional manual live probe" (`implementation/phase-2-impl.md:69`, `implementation/phase-2-impl.md:133`). Make the live probe a concrete secondary/manual verify command with expected output, or include an opt-in pytest marker such as `--run-live-source-probes`; the primary CI command can remain mocked, but the phase cannot be considered verified without a defined real-world probe path.

- **Major**: Source matrix coverage can become self-referential. The plan says tests should prove every row from `source-matrix.md` has a matching source spec (`implementation/phase-2-impl.md:109`), but it does not say whether tests parse the Markdown matrix, use a checked-in fixture extracted from it, or only inspect `mcp/legal_texts/sources.py`. If tests use the same constants as the implementation, they will not catch omissions like missing BDSG, wrong `ttdsg`, wrong `pangv_2022`, or missing invalid-path probes. Specify a separate expected-ID/URL oracle derived from `source-matrix.md`, including all 9 German laws, DSGVO, `tddsg` 404, and `pangv` 404.

- **Minor**: The proposed verify command does not explicitly assert importer-only independence from `bundestag/gesetze`. Existing legacy code legitimately contains `raw.githubusercontent.com/bundestag/gesetze` in `mcp/parser.py:288`, so a repository-wide ban would be wrong. Add a focused test that `mcp/legal_texts/sources.py` and the importer do not use Bundestag GitHub URLs or `prepare_data` outputs as productive source inputs.

### Real-World Testing

Real-world testing is acknowledged but not planned concretely. The default pytest command should stay deterministic and mocked, but Phase 2 needs an explicit live probe command or documented manual step that exercises the same source specs against current `gesetze-im-internet.de` and Publications Office URLs, including XML content type and expected 404 invalid paths.

## Reference Consistency

### Findings

- All code anchors used by the implementation plan are real: `prepare_data/prepare_gesetze_im_internet.sh`, `mcp/parser.py`, `mcp/config.py`, `Dockerfile`, and `.gitignore` exist. The cited legacy behavior is accurate: `LawLibrary.load_laws_from_github` builds Bundestag raw URLs (`mcp/parser.py:278`), `Settings.load_from_folder` defaults to `/app/gesetze/` (`mcp/config.py:5`), and Docker clones `bundestag/gesetze` (`Dockerfile:6`).

## Reality Check Validation

### Findings

- The Reality Check is mostly honest: Phase 2 adds new import code without switching runtime serving, and it correctly identifies that Phase 4/7 own normalized consumption and runtime migration (`implementation/phase-2-impl.md:148`). The missing piece is verification: the Reality Check says live probe expectations remain documented while default pytest mocks network (`implementation/phase-2-impl.md:152`), but it does not provide the alternate command or artifact that proves those live expectations after Phase 2.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Testing / Real-world verification | Live source probing is in Phase 2 scope but not in a concrete verify path. | Add an opt-in live probe command or pytest marker with expected output for all matrix URLs, DSGVO Cellar XML, and invalid-path 404s. |
| 2 | Major | DSGVO / Source metadata | DSGVO Cellar metadata validation is too vague for CELEX, Cellar work, expression, language, content type, and hash. | Add explicit fields and importer checks for the matrix metadata, not only the URL and XML content type. |
| 3 | Major | Documentation / Scope | Documentation of supported and known-issue source entries is a Phase 2 deliverable but no doc edit is planned. | Add a documentation step and list the target docs/artifact. |
| 4 | Major | Testing / Source matrix | Matrix coverage tests may be self-referential if they only inspect implementation constants. | Specify a separate matrix oracle parsed from `source-matrix.md` or a checked expected table. |
| 5 | Minor | Manifest schema | `snapshot_id` storage and `dataset_id` manifest schema are not reconciled. | Define the Phase 2 manifest identity fields before implementation. |
| 6 | Minor | Source dependency | Importer-only no-Bundestag dependency is stated but not directly testable. | Add a focused assertion over `mcp/legal_texts` source specs/importer behavior. |
| 7 | Minor | Stand-date metadata | `stand_date_status` is required by the matrix but not placed in the model shape. | Define the exact serialized status/issue fields and validation behavior. |

## Recommendations

1. Add a concrete live source verification path that runs after implementation and exercises the same source specs against real upstream URLs.
2. Expand Step 1/3/6 to model and validate DSGVO Cellar metadata fields exactly as required by `source-matrix.md`.
3. Add the missing documentation update step for supported source entries, known issues, invalid paths, and the legacy runtime boundary.
4. Tighten source-matrix tests so they compare implementation specs to an independent matrix oracle rather than to themselves.
5. Clarify manifest identity and stand-date status serialization before coding.
