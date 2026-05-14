---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 2
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 2 - Reproducible Source Import

> Implements [Phase 2](../phases/phase-2.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 2 introduces a reproducible source import layer without replacing runtime serving yet. The work is to add typed source specifications from the Phase 1 source matrix, implement deterministic probing/downloading for `gesetze-im-internet.de` XML ZIP files and the DSGVO Cellar act XML artifact, write raw snapshots and manifests to the Phase 1 dataset layout, and cover validation/error behavior with tests. Existing Markdown parser and MCP tool behavior remain unchanged until later phases.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| `mcp/legal_texts/importer.py` | create | Source probing, downloading, hashing, raw snapshot writing, and manifest generation. |
| `mcp/legal_texts/sources.py` | create | Phase 1 source specifications derived from `source-matrix.md`, including invalid-path regression probes. |
| `mcp/legal_texts/models.py` | create | Shared Phase 1 data records needed by import: source metadata, raw snapshot records, manifest records, and validation result records. |
| `mcp/legal_texts/errors.py` | create | Structured import/source errors using the approved error codes. |
| `mcp/tests/test_source_import.py` | create | Unit and fixture tests for import, manifest hashing, stable manifests, failures, and raw/manifest layout. |
| `mcp/tests/test_source_matrix.py` | create | Tests for source specification coverage and invalid path regression expectations. |
| `mcp/tests/fixtures/source_matrix_expected.json` | create | Independent expected source table used as the test oracle for matrix/spec coverage. |
| `mcp/tests/fixtures/raw/` | create/modify | Small deterministic raw fixture artifacts used by import tests. |
| `.gitignore` | modify | Ignore full local import snapshots under `data/sources/raw/` and `data/normalized/` while keeping committed test fixtures. |
| `docs/features/data-preparation.md` | modify | Document the new reproducible source import path, safely supported Phase 2 sources, known invalid paths, and legacy runtime boundary. |
| `docs/modules/data-preparation.md` | modify | Document the importer module relationship to the existing `prepare_data` helper workflow. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global source, manifest, validation, and no-`bundestag/gesetze` requirements. |
| `plans/reliable-law-data-mcp/phases/phase-2.md` | Gated Phase 2 scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | Dataset layout, source metadata, raw snapshot, manifest, readiness, and error contracts. |
| `plans/reliable-law-data-mcp/source-matrix.md` | Canonical source rows, valid URLs, invalid-path regression requirements, and DSGVO Cellar metadata. |
| `plans/reliable-law-data-mcp/implementation/phase-1-impl.md` | Prior implementation decisions and verify constraints. |
| `docs/overview.md` | Current project structure and test command context. |
| `docs/features/data-preparation.md` | Existing data-preparation documentation that still reflects demo tooling. |
| `docs/modules/data-preparation.md` | Current module inventory for the external `gesetze-tools` helper path and likely Phase 2 doc target. |
| `docs/modules/container-runtime.md` | Documents the Docker legacy data dependency that Phase 2 must not reinforce. |
| `prepare_data/prepare_gesetze_im_internet.sh` | Existing preparation script clones `gesetze-tools`; it is an anchor but not the new import implementation. |
| `mcp/parser.py` | Current GitHub URL loader remains a known legacy path until later phases. |
| `mcp/tests/conftest.py` | Existing pytest fixture style and baseline parser test setup. |
| `Dockerfile` | Current image still clones `bundestag/gesetze`; Phase 2 must not add a second production demo-data dependency. |

## Phase 2 Model Clarifications

Phase 2 raw manifests use the Phase 1 contract records with these concrete serialization rules:

- `ManifestRecord.dataset_id` and `ManifestRecord.snapshot_id` both equal the raw snapshot directory name for Phase 2 manifests under `data/sources/raw/{snapshot_id}/manifest.json`.
- Every `SourceMetadata` object includes `stand_date`, `stand_date_status`, `stand_date_issue`, `content_hash`, `source_url`, `retrieved_at`, `source_kind`, `source_identifier`, and `source_metadata`.
- `stand_date_status` is one of `present`, `not_exposed`, or `known_issue`; `stand_date_issue` is `null` unless `stand_date_status` is `known_issue`.
- German `source_metadata` contains `source_path`.
- DSGVO `source_metadata` contains `celex="32016R0679"`, `cellar_work="3e485e15-11bd-11e6-ba9a-01aa75ed71a1"`, `expression="0004.02"`, `language="DE"`, `document="DOC_2"`, and optional `toc_document="DOC_1"` when the metadata/TOC artifact is stored.
- Probe records distinguish importable source probes from regression-only invalid-path probes so expected 404 rows are recorded but never downloaded.

## Implementation Steps

### Step 1: Add Shared Import Records and Errors

- **What**: Create JSON-compatible records for source metadata, raw snapshot entries, manifest records, source probe results, validation summaries, and structured errors.
- **Where**: `mcp/legal_texts/models.py` and `mcp/legal_texts/errors.py`.
- **Why**: Import, normalization, readiness, MCP, and HTTP need one provenance and error shape rather than ad hoc dictionaries.
- **Considerations**: Keep records serializable with the standard library. Include the Phase 2 model clarification fields exactly. Use approved codes `SOURCE_UNAVAILABLE` and `DATASET_NOT_READY` for import/readiness failures. Do not introduce legal interpretation fields.

### Step 2: Encode Source Specifications From the Matrix

- **What**: Add source specs for BGB, EGBGB, DDG, UWG, TDDDG/TTDSG, BDSG, BFSG, VSBG, PAngV, and DSGVO, plus invalid-path probes for `tddsg` and `pangv`.
- **Where**: `mcp/legal_texts/sources.py`.
- **Why**: Source paths must be data-driven and auditable, not inferred from aliases or display codes.
- **Considerations**: `tdddg` uses upstream path `ttdsg`; `pangv_2022` uses upstream path `pangv_2022`; DSGVO uses source kind `eur-lex-cellar` and the official German Cellar act XML URL ending in `DOC_2`. `DOC_1` is metadata/TOC only and may be an auxiliary source, never the article source. Keep aliases for Phase 3 registry work, but do not implement user alias resolution here. Tests must compare specs to `mcp/tests/fixtures/source_matrix_expected.json`, not only to implementation constants.

### Step 3: Implement Source Probing

- **What**: Implement probe behavior that checks expected status, content type where required, URL, source kind, and invalid-path expectations before accepting an import.
- **Where**: `mcp/legal_texts/importer.py`.
- **Why**: Import must fail before writing a trusted snapshot when canonical sources are unavailable or no longer match the matrix.
- **Considerations**: Treat expected 404 probes as passing regression checks, not importable sources. Use bounded timeouts and deterministic probe result records. Tests should mock HTTP responses by default. Add a required opt-in live probe path, for example `PYTHONPATH=mcp python3 -m legal_texts.importer --probe-live`, that prints a summary including all expected 200 checks, both expected 404 checks, and the DSGVO XML content-type result.

### Step 4: Validate DSGVO Cellar Metadata

- **What**: Validate that the DSGVO source spec and downloaded/probed artifact record CELEX `32016R0679`, Cellar work `3e485e15-11bd-11e6-ba9a-01aa75ed71a1`, expression `0004.02`, language `DE`, document `DOC_2`, XML content type, `<LG.DOC>DE</LG.DOC>`, `<ACT` article-bearing content, source URL, content hash, and byte size.
- **Where**: `mcp/legal_texts/sources.py`, `mcp/legal_texts/importer.py`, and `mcp/tests/test_source_import.py`.
- **Why**: DSGVO is an official EU source and must remain separate from the German `gesetze-im-internet` pipeline with explicit provenance.
- **Considerations**: Do not depend on the human-facing EUR-Lex `TXT` URL for machine import. Do not treat `DOC_1` as article XML; it is metadata/TOC with `REF.PHYS`. Tests can validate metadata from source specs and mocked XML bytes; the live probe confirms URL/content-type and article-bearing content availability.

### Step 5: Implement Raw Snapshot Download and Hashing

- **What**: Download raw source artifacts, compute SHA-256 hashes, store bytes under `data/sources/raw/{snapshot_id}/`, and record byte size and retrieval timestamp.
- **Where**: `mcp/legal_texts/importer.py`.
- **Why**: Reproducibility requires retaining raw source material separately from normalized data.
- **Considerations**: Use explicit `snapshot_id` input for deterministic tests; default runtime snapshot IDs may use UTC timestamps. Do not unpack XML ZIPs in Phase 2 except where needed to detect source-level metadata; deep structural normalization belongs to Phase 4.

### Step 6: Generate and Compare Manifests

- **What**: Write `manifest.json` with source metadata, raw paths, hashes, stand-date status, validation summary, and deterministic entry ordering; add comparison helpers for changed hashes/entries.
- **Where**: `mcp/legal_texts/importer.py` and `mcp/legal_texts/models.py`.
- **Why**: Snapshot changes must be visible and testable between imports.
- **Considerations**: Manifest ordering must be stable. Use the Phase 2 rule that `dataset_id == snapshot_id` for raw manifests. For sources where stand date is not extracted in Phase 2, record `stand_date_status` as `not_exposed` or `known_issue` according to the contract rather than omitting it.

### Step 7: Add Fixture-Backed Import Tests

- **What**: Test stable hashing/manifests, expected probe validation, invalid-path regression probes, unavailable-source failures, DSGVO metadata/content-type validation, manifest diff behavior, independent source matrix coverage, and importer-only no-Bundestag source dependency.
- **Where**: `mcp/tests/test_source_import.py`, `mcp/tests/test_source_matrix.py`, `mcp/tests/fixtures/source_matrix_expected.json`, and `mcp/tests/fixtures/raw/`.
- **Why**: Phase 2 must be testable without relying on the network, while still preserving the source matrix expectations.
- **Considerations**: Use mocked `urllib.request.urlopen` or an injectable fetcher. The source-matrix oracle must explicitly list all nine German laws, DSGVO, valid source URLs, `tddsg` expected 404, and `pangv` expected 404. A focused test may scan only `mcp/legal_texts/sources.py` and `mcp/legal_texts/importer.py` for `bundestag/gesetze` URLs so legacy runtime files are not falsely flagged. Existing `mcp/tests/test_parser.py` and `mcp/tests/test_library.py` should keep passing unchanged.

### Step 8: Update Source Import Documentation

- **What**: Document supported Phase 2 source entries, known invalid paths, DSGVO Cellar provenance, manifest fields, local snapshot directories, and the boundary that existing runtime/Docker still migrate later.
- **Where**: `docs/features/data-preparation.md`, `docs/modules/data-preparation.md`, and links from `docs/overview.md` if a new import section is added.
- **Why**: Phase 2 explicitly requires documentation of which laws are safely supported and which source limitations are known.
- **Considerations**: Do not claim runtime serving has switched to the new dataset yet. State that `bundestag/gesetze` remains only in legacy runtime/demo paths until Phase 7 removes it.

### Step 9: Protect Local Snapshot Directories

- **What**: Add ignore rules for local full import output while keeping committed fixtures under `mcp/tests/fixtures/`.
- **Where**: `.gitignore`.
- **Why**: Real source snapshots can be large and should not be accidentally committed as runtime data.
- **Considerations**: Do not ignore `mcp/tests/fixtures/raw/` or golden outputs required by later phases.

## Testing Plan

Primary verify command:

```bash
PYTHONPATH=mcp python3 -m pytest mcp/tests/test_source_matrix.py mcp/tests/test_source_import.py mcp/tests/test_parser.py mcp/tests/test_library.py
```

Required live source verification command before Phase 2 is marked complete:

```bash
PYTHONPATH=mcp python3 -m legal_texts.importer --probe-live
```

Expected live command output must include a successful summary for 18 importable German index/XML ZIP probes, the DSGVO Cellar `DOC_2` XML probe with XML content type, `<LG.DOC>DE</LG.DOC>`, and `<ACT` content, and two passing invalid-path regression probes for `tddsg` and `pangv` expected 404 responses.

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Source spec coverage | Compare `mcp/legal_texts/sources.py` and `source-matrix.md` against `mcp/tests/fixtures/source_matrix_expected.json`. | Tests catch missing IDs, wrong source paths, wrong URLs, and missing invalid-path probes. |
| Probe validation | Expected 200, expected 404, DSGVO XML content type, and source-unavailable scenarios. | Passing probes return structured records; failing probes raise structured source errors. |
| Live source probes | Opt-in live command checks current upstream status and content type from the source specs. | Command reports all expected 200/404/XML checks as passing before phase completion. |
| DSGVO metadata | CELEX, Cellar work, expression `0004.02`, language `DE`, document `DOC_2`, source URL, XML content type, `<LG.DOC>DE</LG.DOC>`, `<ACT`, and hash are recorded. | Manifest/source metadata match `source-matrix.md`, reject metadata-only `DOC_1` as the article source, and reject Dutch `0017.02` for German fixtures. |
| Snapshot import | Raw bytes write under the configured snapshot directory with SHA-256 hashes, sizes, URLs, and retrieval timestamps. | Manifest entries match fixture hashes and paths. |
| Manifest reproducibility | Repeated import over unchanged fixture bytes with the same snapshot ID has stable manifest semantics. | Stable hashes and deterministic entry ordering. |
| Manifest diff | Changed fixture bytes produce a machine-readable changed-entry result. | Diff helper reports changed canonical IDs/hashes. |
| Importer source independence | New `mcp/legal_texts` import path does not reference Bundestag demo-data URLs or `prepare_data` outputs as productive sources. | Focused test passes while legacy runtime files may still contain deferred dependencies. |
| Documentation | Supported sources, known invalid paths, DSGVO provenance, manifest fields, and runtime boundary are documented. | Docs reflect Phase 2 behavior without claiming Phase 7 runtime migration. |
| Existing parser/library tests | Current demo parser behavior remains unchanged during Phase 2. | Existing tests still pass. |

### Test Integrity Constraints

- `mcp/tests/test_parser.py` and `mcp/tests/test_library.py` must remain behaviorally unchanged unless imports require path-only test setup changes.
- New import tests must not perform live network requests by default; they should mock transport/fetching for deterministic CI.
- The live source command is required for phase completion but should remain opt-in outside CI unless explicitly configured.
- Phase 2 tests must not weaken the later requirement to remove `bundestag/gesetze`; they only ensure the new import layer does not depend on it.

## Rollback Strategy

Remove `mcp/legal_texts/importer.py`, `mcp/legal_texts/sources.py`, the import-related model/error records if unused by later phases, the new source import tests/fixtures, and the `.gitignore` data-output entries. Runtime parser/MCP behavior should remain as it was before this phase.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| HTTP client | `urllib.request` / `requests` / external CLI | `urllib.request` with injectable fetcher | Keeps runtime dependencies small and easy to mock. |
| Snapshot ID default | required argument only / UTC timestamp default / content-derived ID | explicit argument with UTC timestamp default | Tests can be deterministic while local imports remain convenient. |
| Stand date extraction | parse all upstream formats now / record status only / defer entirely | record status with lightweight metadata only | Phase 2 owns raw provenance; structural parsing belongs to Phase 4. |
| Network in tests | live source probes in pytest / mocked by default / no probes | mocked by default | Stable tests should not depend on source-site availability; source specs still preserve live expectations. |
| Live source verification | mandatory default pytest / opt-in module command / manual curl checklist | opt-in module command required before phase completion | Keeps CI deterministic while still satisfying Phase 2 real-world source probing. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `prepare_data/prepare_gesetze_im_internet.sh` | `git clone https://github.com/bundestag/gesetze-tools` and conversion flow | Existing data preparation is external-tool based and not a reproducible Phase 1 source snapshot pipeline. |
| `mcp/parser.py` | `LawLibrary.load_laws_from_github` | Current loader still fetches `bundestag/gesetze` Markdown; Phase 2 adds new import code without switching runtime loading. |
| `mcp/parser.py` | `LawLibrary.load_laws_from_folder` | Current folder loader expects `index.md`, not raw official XML ZIP snapshots. |
| `mcp/config.py` | `Settings.load_from_folder` | Runtime default still points at `/app/gesetze/`; migration is planned for Phase 7, not Phase 2. |
| `Dockerfile` | `git clone https://github.com/bundestag/gesetze.git` | Container migration is out of Phase 2 scope but must not be reinforced by new import code. |
| `.gitignore` | Python ignore template, no data layout rules | Needs explicit local data ignores for full snapshots. |

### Mismatches / Notes

- Existing runtime code cannot consume Phase 2 raw snapshots yet; Phase 4 normalizes them and Phase 7 switches runtime loading.
- The existing `prepare_data` script references `gesetze-tools`; Phase 2 should add the new reproducible importer rather than trying to retrofit that shell script.
- Live source probe expectations are covered by the opt-in `legal_texts.importer --probe-live` command; default pytest coverage should mock network behavior to stay deterministic.
