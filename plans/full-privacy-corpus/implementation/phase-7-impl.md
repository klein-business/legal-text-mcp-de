---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 7
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 7 - EU neighbor acts source family

> Implements [Phase 7](../phases/phase-7.md) of [full-privacy-corpus](../plan.md)

## Approach

Generalize the Phase 5 EUR-Lex/Cellar parser and source metadata path from DSGVO to bounded EU neighbor acts supplied by the Phase 6 seed graph, starting with AI Act CELEX `32024R1689` and Data Act CELEX `32023R2854`. Import official German text where available; otherwise emit manifest source limitations.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Add EU neighbor source specs, generic EUR-Lex parser flow, fixtures, limitations, and validation tests. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-7.md` | Gated bounded EU neighbor scope. |
| `plans/full-privacy-corpus/implementation/phase-5-impl.md` | DSGVO parser and Cellar metadata policy to reuse. |
| `plans/full-privacy-corpus/implementation/phase-6-impl.md` | Approved seed graph and CELEX source list. |
| `mcp/legal_texts/data/privacy_scope_seed.v1.json` | Phase 6 seed graph source of truth for AI Act/Data Act CELEX and canonical IDs. |
| `mcp/legal_texts/eurlex_xml.py` | Current DSGVO-specific parser to generalize. |
| `mcp/legal_texts/sources.py` | Existing `SourceSpec` shape and DSGVO Cellar metadata example. |
| `mcp/legal_texts/manifest.py` | Source limitation and terminal-state validation. |
| `mcp/legal_texts/validation.py` | Package validation for new units and manifest references. |
| `mcp/legal_texts/relationships.py` | Relationship target validation from Phase 6/Phase 2. |
| `mcp/tests/test_normalizer_eurlex.py` | Existing EUR-Lex parser test pattern. |
| `docs/features/source-provenance.md` | Documentation target for CELEX/language/version policy. |

## Implementation Steps

### Step 1: Add bounded EU neighbor source records

- **What**: Add source records for AI Act (`32024R1689`) and Data Act (`32023R2854`) by consuming or validating against the Phase 6 seed graph, including canonical IDs, language/version policy fields, official URL metadata, and imported-or-limited expected outcomes.
- **Where**: `mcp/legal_texts/sources.py` or new generated source-spec builder fed by `mcp/legal_texts/data/privacy_scope_seed.v1.json`.
- **Why**: The phase must start with explicit seed CELEX records, not an unbounded EU importer.
- **Seed validation**: Fail fast if the seed file is missing, lacks AI Act/Data Act records, or has CELEX/canonical ID values that diverge from the source records generated in this phase.
- **Considerations**: Preserve DSGVO source behavior and canonical ID `dsgvo_eu_2016_679`; do not infer new EU acts outside the approved Phase 6 seed graph.

### Step 2: Generalize EUR-Lex parsing

- **What**: Refactor `parse_dsgvo_xml` into reusable parsing helpers for article, recital, chapter, section, and annex-like structures where present, while keeping a DSGVO wrapper for compatibility.
- **Where**: `mcp/legal_texts/eurlex_xml.py`.
- **Why**: AI Act and Data Act use official EUR-Lex/Cellar structures but should not require copied DSGVO-specific parser code.
- **Expected outputs**: Define expected `unit`, `norm_id`, `status`, title/text, children, and source URL behavior for articles, recitals, chapters, sections, annexes, and unsupported structures in fixture tests.
- **Considerations**: Unsupported structures should produce `unsupported_format` or `parse_failed` source states with diagnostics, not partial silent imports.

### Step 3: Add fixtures and source limitation records

- **What**: Add representative AI Act and Data Act fixtures when official German text is reachable; add limitation fixtures for unreachable or unsupported official sources.
- **Where**: `mcp/tests/fixtures/eurlex/`; `mcp/tests/test_eu_neighbor_acts.py`.
- **Why**: Acceptance requires imported-or-limited behavior for seeded EU acts.
- **Evidence artifact**: Add `scripts/verify_eu_neighbor_sources.py --seed mcp/legal_texts/data/privacy_scope_seed.v1.json --output .artifacts/eu-neighbors/evidence.json` to probe/fetch selected official German EUR-Lex/Cellar URLs, validate imported-or-limited terminal states, and persist CELEX/language/version/hash evidence.
- **Considerations**: The fixture may be a small representative slice; full text evidence belongs in generated artifacts.

### Step 4: Validate relationship target readiness

- **What**: Ensure imported EU records or source limitations resolve as valid targets for Phase 6 relationship records.
- **Where**: `mcp/legal_texts/relationships.py`; `mcp/tests/test_relationship_records.py`.
- **Why**: Phase 11 relationship APIs depend on official records or limitations for targets.
- **Considerations**: Do not expose related-norm APIs in this phase.

### Step 5: Document EU CELEX/language/version policy

- **What**: Document the bounded EU neighbor policy, seed-file source of truth, CELEX IDs, German-language selection, version/consolidation policy, and imported-or-limited evidence artifact.
- **Where**: `docs/features/source-provenance.md` or a dedicated EU source-policy docs note linked from it.
- **Why**: Phase 7 deliverables require CELEX/language/version policy documentation before broader Phase 13 docs cleanup.
- **Considerations**: Do not document an unbounded EU importer; this phase remains seed-bound.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_eu_neighbor_acts.py mcp/tests/test_normalizer_eurlex.py mcp/tests/test_relationship_records.py`

Opt-in EU source verification command: `PYTHONPATH=mcp uv run --group dev python scripts/verify_eu_neighbor_sources.py --seed mcp/legal_texts/data/privacy_scope_seed.v1.json --output .artifacts/eu-neighbors/evidence.json`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Parser | Representative EU neighbor XML produces validated records with EUR-Lex/Cellar provenance. | AI Act/Data Act fixtures import or classify explicitly. |
| Manifest | Missing or unsupported official EU sources become source limitations. | No seeded EU act is silently omitted. |
| Seed | AI Act/Data Act source records are generated from or validated against `privacy_scope_seed.v1.json`. | Missing or divergent seed records fail. |
| Gate | Opt-in EU source verification writes CELEX/language/version/hash evidence and terminal states. | Official German sources are imported or explicitly limited. |
| Relationship | Phase 6 relationship targets for AI Act/Data Act resolve to imported records or source limitations. | Relationship validation passes without unresolved external targets. |
| Docs | CELEX/language/version policy is documented. | Seed-bound EU scope is clear before runtime APIs consume it. |
| Regression | DSGVO parser behavior from Phase 5 remains unchanged. | Existing EUR-Lex tests pass. |

### Test Integrity Constraints

- Do not broaden import beyond Phase 6 seed graph or explicitly added seed records.
- Do not weaken DSGVO count/version tests to accommodate generic parser changes.
- Source limitations must be tested as first-class outcomes, not skipped cases.

## Rollback Strategy

Revert EU neighbor source records, generic parser refactor, fixtures, and tests. DSGVO-specific parsing should remain usable from Phase 5.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Additional EU acts beyond AI Act/Data Act | Auto-discover; seed-only | Seed-only | Phase scope bounds imports to approved scope graph or explicit seed additions. |
| Unavailable German official text | Omit; source limitation | Source limitation | The plan requires explicit imported-or-limited states. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/eurlex_xml.py` | `parse_dsgvo_xml` | Current parser is DSGVO-specific and article-oriented. |
| `mcp/legal_texts/sources.py` | `SOURCE_SPECS["dsgvo_eu_2016_679"]` | Existing source spec pattern has CELEX, Cellar work, expression, language, and document metadata. |
| `mcp/legal_texts/importer.py` | `validate_dsgvo_doc2` | Current source validation is DSGVO DOC_2-specific and needs generic equivalent for neighbors. |

### Mismatches / Notes

- Current `SourceKind` string is `eur-lex-cellar`; keep that value for serving records even though the Phase 1 manifest source-family table names the family as EUR-Lex/Cellar.
- Current docs mention only DSGVO as an EUR-Lex source; broader EU neighbor docs are deferred to Phase 13.
- Phase 7 still needs a narrow CELEX/language/version policy note; Phase 13 can later fold it into final user-facing docs.
