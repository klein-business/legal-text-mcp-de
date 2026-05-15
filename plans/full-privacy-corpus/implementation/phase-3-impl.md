---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 3
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 3 - Complete GII discovery coverage

> Implements [Phase 3](../phases/phase-3.md) of [full-privacy-corpus](../plan.md)

## Approach

Add a GII TOC discovery path that fetches or parses `gii-toc.xml`, creates one Phase 1 discovery-mode manifest source record per `<item>`, and records discovery count metadata compatible with the Phase 2 generated package. This phase discovers source records only; it must not parse every `xml.zip` payload into legal text or claim terminal import coverage.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Add GII TOC parser/fetcher, discovery manifest writer, fixture tests, and explicit live discovery gate script. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-3.md` | Gated discovery-only scope and acceptance criteria. |
| `plans/full-privacy-corpus/implementation/phase-1-impl.md` | Manifest terminal-state and source-family contract to use. |
| `plans/full-privacy-corpus/implementation/phase-2-impl.md` | Generated package metadata and strict validation targets. |
| `mcp/legal_texts/validation.py` | Phase 2 generated-package validation helper that discovery metadata must satisfy. |
| `mcp/legal_texts/sources.py` | Current hand-maintained `GERMAN_SOURCES` and `SOURCE_SPECS` that discovery must not rely on. |
| `mcp/legal_texts/importer.py` | Current fetch helper, timestamp helper, and raw snapshot manifest pattern. |
| `mcp/legal_texts/manifest.py` | Planned Phase 1 manifest validators and terminal-state constants. |
| `mcp/tests/test_generated_package.py` | Phase 2 generated-package fixture expectations for discovery metadata. |
| `mcp/tests/test_source_import.py` | Current fake fetch style for source probing tests. |
| `docs/features/source-provenance.md` | Provenance docs to extend with complete GII coverage measurement. |
| `docs/features/law-loading-and-indexing.md` | Generated package docs that should mention discovery count metadata. |

## Implementation Steps

### Step 1: Add a GII TOC parser

- **What**: Create `mcp/legal_texts/gii_toc.py` with `parse_gii_toc(content: bytes | str) -> list[dict]` that extracts every `<item>`, stable source path, title/display data where available, index URL, and `xml.zip` URL.
- **Where**: New `mcp/legal_texts/gii_toc.py`.
- **Why**: Phase 3 defines complete GII as every official TOC item, not the current hand-maintained fixture source list.
- **Normalization rules**: For each `<item><link>.../xml.zip</link></item>`, parse the URL, strip a trailing `/xml.zip`, lowercase the final path segment, percent-decode safe path characters, and use that segment as `source_path` and default `source_id` (`gii:<source_path>` in manifest records). Preserve the original link as `xml_zip_url`, derive `index_url` from the parent path, normalize `http://www.gesetze-im-internet.de/...` to `https://www.gesetze-im-internet.de/...` for stored URLs, and preserve the original URL in `source_metadata.original_link`. Existing curated aliases from `mcp/legal_texts/sources.py` must be copied into an `alias_candidates` metadata section rather than replacing the source-path ID. Duplicate normalized `source_path` values are fatal discovery errors.
- **Considerations**: The parser should be namespace-tolerant and preserve unknown-but-useful TOC metadata in a `source_metadata` subobject. The live TOC currently exposes `<item>` records with `<title>` and direct `xml.zip` `<link>` values; tests must still tolerate extra fields or namespaces.

### Step 2: Add discovery manifest generation

- **What**: Add `discover_gii_sources(fetch=default_fetch)` or equivalent that fetches `https://www.gesetze-im-internet.de/gii-toc.xml`, parses all items, and emits one manifest source record per item with source family `gii` for discovery-mode validation. If the TOC itself is unavailable, emit a TOC-level source limitation artifact rather than fake item records.
- **Where**: `mcp/legal_texts/gii_toc.py`; use `mcp/legal_texts/importer.default_fetch`, `utc_now`, and `sha256_bytes`.
- **Why**: Later bulk normalization consumes discovered GII source records rather than `GERMAN_SOURCES`.
- **Failure schema**: A TOC-level limitation record must include `limitation_id="gii-toc:<retrieved_at-or-hash>"`, `source_family="gii"`, `source_id="gii:toc"`, `terminal_state="source_unavailable"` or `parse_failed`, `source_url`, `retrieved_at`, `http_status` or exception code, `reason`, and `details`. Malformed individual TOC items must not silently drop; they should produce item diagnostics with `item_index`, `reason`, and original title/link snippets, and any malformed item should make discovery validation fail unless the item is represented by an explicit diagnostic in the artifact.
- **Considerations**: Do not download each `xml.zip` in this phase. Use `validate_corpus_manifest(..., require_terminal_states=False)` for discovery artifacts; Phase 4 assigns terminal states after fetch/parse attempts.

### Step 3: Write discovery metadata compatible with generated packages

- **What**: Store `discovered_gii_items`, TOC URL, TOC content hash, retrieval timestamp, parser version, normalized source-path count, duplicate count, and malformed-item diagnostics in generated package metadata and manifest summary.
- **Where**: Use the Phase 2 generated-package metadata helper from `mcp/legal_texts/validation.py`; add only a small writer in `mcp/legal_texts/gii_toc.py` if needed to assemble the artifact payload before validation.
- **Why**: Acceptance requires discovery count reporting and live-gate artifact evidence.
- **Artifact contract**: `scripts/verify_gii_discovery.py --output <path>` must write JSON with `schema_version="gii-discovery-artifact.v1"`, `toc_url`, `retrieved_at`, `toc_sha256`, `parser_version`, `discovered_gii_items`, `manifest_path` or embedded `manifest`, `source_paths`, `malformed_items`, `toc_limitation` when present, and `validation_errors`.
- **Considerations**: Every fixture TOC item must have exactly one manifest record; duplicates should fail validation. Run strict generated-package validation for discovery metadata through the Phase 2 helper.

### Step 4: Add fixture tests and live discovery gate

- **What**: Add `mcp/tests/fixtures/gii/gii-toc-sample.xml`, `mcp/tests/test_gii_toc_discovery.py`, and `scripts/verify_gii_discovery.py` for explicit network-heavy discovery that writes a JSON artifact path supplied by CLI or environment.
- **Where**: New GII fixture/test/script files.
- **Why**: Fast tests prove parser and count behavior; the live script gives scheduled or explicit evidence without importing all payloads.
- **Test coverage**: Unit tests must cover mocked successful fetch, non-200 fetch, fetch exception, malformed XML, malformed item, duplicate normalized source path, artifact writing, and strict generated-package validation of discovery metadata.
- **Considerations**: The live script must not run from `scripts/verify_release.py` by default.

### Step 5: Document complete GII coverage measurement

- **What**: Document how complete GII coverage is measured from `gii-toc.xml`, including `discovered_gii_items`, normalized `source_path`, TOC hash, retrieval timestamp, parser version, fixture-vs-live behavior, live artifact schema/path, and the opt-in nature of `scripts/verify_gii_discovery.py`.
- **Where**: `docs/features/source-provenance.md` for official TOC provenance and discovery artifacts; `docs/features/law-loading-and-indexing.md` for generated-package metadata fields that record `discovered_gii_items`.
- **Why**: Phase 3 deliverables require documentation of complete GII coverage measurement, not just parser/script behavior.
- **Considerations**: Do not claim full GII import completeness in this phase; Phase 4 assigns terminal states after payload fetch/parse attempts.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_gii_toc_discovery.py mcp/tests/test_corpus_manifest.py mcp/tests/test_generated_package.py mcp/tests/test_source_import.py && PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`

Opt-in live verification command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_gii_discovery.py --output .artifacts/gii-discovery/latest.json`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Unit | Fixture TOC item count equals generated `discovered_gii_items`. | One manifest record exists for each fixture `<item>`. |
| Unit | TOC link normalization derives deterministic `source_path`, `source_id`, `index_url`, `xml_zip_url`, and alias candidates. | Duplicate normalized source paths fail discovery deterministically. |
| Unit | Duplicate or malformed TOC entries are rejected or classified explicitly. | Discovery-mode validation reports errors without silent drops. |
| Unit | `scripts/verify_gii_discovery.py` writes the artifact schema for mocked success and mocked TOC failure. | Artifact includes count/hash/timestamp/parser-version fields and failure details. |
| Docs | GII coverage measurement docs mention `discovered_gii_items`, TOC hash/timestamp, artifact schema/path, and opt-in live gate. | Docs explain discovery coverage without claiming terminal import coverage. |
| Regression | Existing source import helper tests still pass. | Current fixture source probing remains intact. |

### Test Integrity Constraints

- Do not change `mcp/tests/test_source_matrix.py` to redefine current fixture source semantics.
- Do not skip or weaken `mcp/tests/test_source_import.py`; discovery should reuse fetch/test patterns without breaking existing source probing.
- The live discovery script must be opt-in and must not make ordinary PR verification network-heavy.

## Rollback Strategy

Remove `mcp/legal_texts/gii_toc.py`, the GII TOC fixtures/tests, the live discovery script, and docs updates. Existing static `SOURCE_SPECS` importer behavior remains available.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| TOC fetch failure representation | Raise only; write source limitation artifact | Write source limitation artifact for explicit gate runs | The plan requires reproducible source failures and persisted artifacts. |
| Discovery script scheduling | Add to release gate; keep opt-in | Keep opt-in | Network-heavy checks must not run on every PR. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/sources.py` | `GERMAN_SOURCES`, `SOURCE_SPECS` | Current discovery is a fixed curated set, not full GII TOC coverage. |
| `mcp/legal_texts/importer.py` | `default_fetch`, `utc_now`, `sha256_bytes`, `import_snapshot` | Existing fetch/hash/timestamp tools can ground TOC discovery. |
| `mcp/tests/test_source_import.py` | `fake_fetch` | Shows the current unit-test pattern for network code. |
| `scripts/verify_release.py` | `selected_tests()` | Confirms network-heavy discovery should not be added to the default release gate. |

### Mismatches / Notes

- Current `import_snapshot` loops over `SOURCE_SPECS.values()` and cannot discover new GII items.
- Phase 3 discovery artifacts are intentionally not terminal coverage manifests; Phase 4 is the first phase that should require exactly one terminal state for every discovered GII item.
- The current source docs mention GII source paths from a source matrix, not complete TOC coverage measurement.
- `mcp/legal_texts/manifest.py`, generated-package helpers, and `mcp/tests/test_generated_package.py` are Phase 1/2 prerequisite outputs, not current baseline files before those phases execute.
- A sampled live TOC shape on 2026-05-15 uses `<item>` elements with `<title>` and direct `<link>` values pointing at `xml.zip` downloads; the parser must remain tolerant of future extra fields or namespaces.
