---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 5
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 5 - Full DSGVO articles and recitals

> Implements [Phase 5](../phases/phase-5.md) of [full-privacy-corpus](../plan.md)

## Approach

Generalize the existing DSGVO Cellar parser from selected article fixtures to full official German-language article and recital extraction for CELEX `32016R0679`. Record the selected Cellar work/expression/document/version policy and emit article `art:*` and recital `recital:*` citation units that validate under the Phase 2 package contract.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Extend EUR-Lex parsing, source metadata validation, resolver/search fixtures, and DSGVO version policy evidence. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-5.md` | Gated DSGVO article/recital scope and counts. |
| `plans/full-privacy-corpus/implementation/phase-2-impl.md` | Package support for `recital` and other new citation units. |
| `mcp/legal_texts/eurlex_xml.py` | Current `parse_dsgvo_xml` article parser. |
| `mcp/legal_texts/sources.py` | Existing DSGVO CELEX/Cellar source metadata and DOC_2 URL. |
| `mcp/legal_texts/importer.py` | `validate_dsgvo_doc2` and source metadata creation. |
| `mcp/legal_texts/models.py` | `NormUnit`, `normalize_unit()`, and `canonical_norm_id()` runtime support for structured `recital` calls. |
| `mcp/legal_texts/resolver.py` | Current exact citation parsing that must accept new units additively. |
| `mcp/legal_texts/search.py` | Search indexing over text-bearing norms. |
| `mcp/legal_texts/validation.py` | Generated-package validation for `art` and `recital` records from Phase 2. |
| `mcp/legal_texts/manifest.py` | Terminal-state and EUR-Lex provenance vocabulary from Phase 1. |
| `mcp/tests/test_normalizer_eurlex.py` | Existing Cellar parser tests. |
| `mcp/tests/test_resolver.py` | Existing resolver compatibility tests. |
| `docs/features/supported-laws.md` | Documentation target for current selected DSGVO fixture coverage and generated full article/recital support. |
| `docs/features/law-loading-and-indexing.md` | Citation-unit documentation target for `recital:*`. |

## Implementation Steps

### Step 1: Record the DSGVO Cellar version policy

- **What**: Add a small policy record or fixture metadata asserting CELEX `32016R0679`, German language, selected Cellar work/expression/document, consolidation/corrigenda policy, retrieval timestamp, and content hash.
- **Where**: `mcp/legal_texts/sources.py` metadata and/or a generated-package metadata fixture.
- **Why**: Acceptance requires tests or source checks that fail if an unintended German expression/document is selected.
- **Count gate linkage**: The policy record must include expected official counts (`article_count=99`, `recital_count=173`) and the selected source hash/version evidence used by the generated full-count gate.
- **Considerations**: Preserve existing `dsgvo_eu_2016_679` canonical ID and aliases.

### Step 2: Extend the EUR-Lex parser for full articles

- **What**: Ensure `parse_dsgvo_xml` extracts all articles 1-99 from official German DOC_2/Formex XML and preserves titles, text, subdivisions, source URL anchors, and source metadata.
- **Where**: `mcp/legal_texts/eurlex_xml.py`; `mcp/tests/test_eurlex_dsgvo_full.py`.
- **Why**: Current fixtures cover selected articles only.
- **Considerations**: Do not hard-code fixture-only article numbers; test fixture can be reduced but parser/gate must support full counts.

### Step 3: Add recital extraction as first-class norms

- **What**: Implement recital extraction that emits `norm_id="recital:<n>"`, `unit="recital"`, stable canonical IDs, active text, URL anchors, and source metadata.
- **Where**: `mcp/legal_texts/eurlex_xml.py`; `mcp/legal_texts/models.py` and `validation.py` already expanded in Phase 2.
- **Why**: The phase requires all 173 DSGVO recitals as citation units.
- **Considerations**: Recitals are not legal articles; keep the unit explicit so relationship APIs can distinguish them later.

### Step 4: Add resolver and search fixtures

- **What**: Extend model-level unit normalization/canonical ID construction and resolver parsing to support `recital:*` exact references and structured `unit="recital"` calls for DSGVO, plus search fixtures that index recital text.
- **Where**: `mcp/legal_texts/models.py`; `mcp/legal_texts/resolver.py`; `mcp/tests/test_resolver.py`; `mcp/tests/test_search.py`; fixture package under `mcp/tests/fixtures/normalized/`.
- **Why**: Acceptance requires `dsgvo_eu_2016_679/art:*` and `dsgvo_eu_2016_679/recital:*` resolver tests.
- **Structured resolver cases**: Add tests for exact `recital:<n>` lookup and structured `resolve_citation(..., unit="recital", paragraph_or_article="<n>")` so `normalize_unit("recital")` and `canonical_norm_id("recital", "<n>")` are exercised.
- **Considerations**: Existing selected DSGVO article behavior must remain backwards compatible.

### Step 5: Add DSGVO full-count gate evidence

- **What**: Add an explicit generated/live artifact checker for official DSGVO count evidence that verifies articles 1-99 and recitals 1-173, selected CELEX/Cellar metadata, source hash, version/consolidation policy, and resolver availability for sampled boundary IDs (`art:1`, `art:99`, `recital:1`, `recital:173`).
- **Where**: New `scripts/verify_dsgvo_full_counts.py`; tests in `mcp/tests/test_eurlex_dsgvo_full.py` using fixture or mocked generated artifacts.
- **Why**: Fast fixtures may stay reduced, but Phase 5 acceptance requires generated corpus checks proving full article and recital coverage.
- **Considerations**: Keep the gate opt-in unless included through a fixture-backed test; do not fabricate full counts in small XML fixtures.

### Step 6: Document DSGVO article and recital citation units

- **What**: Add a scoped docs update for DSGVO `art:*` and `recital:*` citation units, full generated-count evidence, and fixture-vs-generated coverage boundaries.
- **Where**: `docs/features/supported-laws.md` for DSGVO coverage and counts; `docs/features/law-loading-and-indexing.md` for `recital:*` citation-unit/package behavior.
- **Why**: Phase 5 deliverables require article and recital citation-unit documentation before the broader Phase 13 docs pass.
- **Considerations**: Keep final cross-source diagrams and runtime API docs deferred to Phase 13; this step only documents the new DSGVO unit semantics and source evidence.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_eurlex_dsgvo_full.py mcp/tests/test_normalizer_eurlex.py mcp/tests/test_resolver.py mcp/tests/test_search.py mcp/tests/test_generated_package.py && SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`

Opt-in full-count command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_dsgvo_full_counts.py --package-dir .artifacts/dsgvo/package --output .artifacts/dsgvo/full-counts.json`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Parser | Article and recital fixture XML emit expected `art:*` and `recital:*` records. | Records validate and carry Cellar provenance. |
| Source policy | Selected CELEX, language, expression, document, version policy, and content hash are recorded. | Wrong expression/document fixtures fail. |
| Resolver/Search | DSGVO articles and recitals resolve and search without changing existing article behavior. | Positive and negative resolver cases are deterministic. |
| Gate | Full-count artifact verifies 99 articles and 173 recitals with source metadata and boundary resolver samples. | Missing article/recital counts or wrong source metadata fail. |
| Docs | DSGVO `art:*` and `recital:*` citation units are documented in the scoped feature docs. | Users can distinguish selected fixtures from generated full-count evidence. |

### Test Integrity Constraints

- Existing `mcp/tests/test_normalizer_eurlex.py::test_eurlex_parser_requires_doc2_article_xml` must still pass.
- Existing DSGVO article fixture aliases and search behavior must remain compatible.
- Do not fake the 1-99 and 1-173 full counts in fast fixtures; full counts belong in generated or explicit gate artifacts.
- Do not weaken Phase 2 generated-package unit validation to accept malformed recital records.

## Rollback Strategy

Revert EUR-Lex parser changes, new recital fixtures/tests, resolver additions for `recital`, and DSGVO version policy fixture updates. Existing selected article parser behavior returns to Phase 4 state.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Recital unit ID prefix | `recital:<n>`; `rec:<n>` | `recital:<n>` | Matches the plan terminology and is self-describing. |
| Full-count proof location | Fast fixture; generated/live artifact | Generated/live artifact | Fast CI should stay small while explicit gates prove full import counts. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/eurlex_xml.py` | `parse_dsgvo_xml`, `_article_value`, `_article_title` | Current parser only iterates `ARTICLE` elements. |
| `mcp/legal_texts/sources.py` | `SOURCE_SPECS["dsgvo_eu_2016_679"]` | Current Cellar metadata already pins CELEX, work, expression, language, and document. |
| `mcp/legal_texts/importer.py` | `validate_dsgvo_doc2` | Current source validation checks article-bearing German DOC_2 XML but not recital/full-count evidence. |
| `mcp/legal_texts/models.py` | `NormUnit`, `normalize_unit`, `canonical_norm_id` | Structured resolver calls depend on model-level unit normalization and canonical ID construction. |
| `mcp/legal_texts/resolver.py` | `CANONICAL_NORM_RE`, `VALUE_RE` | Current resolver only accepts `par` and `art` exact references. |

### Mismatches / Notes

- `NormUnit` and resolver support for `recital` depend on Phase 2; do not attempt Phase 5 before that lands.
- Current docs say the fixture covers selected DSGVO articles only; final docs update is Phase 13, but tests/fixtures may need local comments or metadata now.
- Phase 5 must update the narrow DSGVO citation-unit docs immediately; Phase 13 can later reorganize or expand the broader docs set.
