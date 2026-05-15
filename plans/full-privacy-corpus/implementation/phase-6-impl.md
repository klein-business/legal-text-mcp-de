---
type: planning
entity: implementation-plan
plan: "full-privacy-corpus"
phase: 6
status: draft
created: "2026-05-15"
updated: "2026-05-15"
---

# Implementation Plan: Phase 6 - DSGVO scope policy and seed graph inventory

> Implements [Phase 6](../phases/phase-6.md) of [full-privacy-corpus](../plan.md)

## Approach

Turn the `dsgvo-gesetz.de`-style scope graph into a governed metadata input. Add a policy decision record, a manually maintainable fallback seed graph, validation for relationship-source records, and transformation rules into the Phase 2 `relationships.json` schema. This phase does not import neighbor full text or expose runtime relationship APIs.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | modify/create | Add scope graph policy data, seed graph fixtures, relationship transformation validation, and source limitation records. |

## Required Context

| File | Why |
|------|-----|
| `plans/full-privacy-corpus/phases/phase-6.md` | Gated policy, seed graph, and no-editorial-copy scope. |
| `plans/full-privacy-corpus/implementation/phase-1-impl.md` | Source limitation and policy-exclusion terminal states. |
| `plans/full-privacy-corpus/implementation/phase-2-impl.md` | Relationship package schema and target validation. |
| `plans/full-privacy-corpus/implementation/phase-5-impl.md` | DSGVO article and recital target ID rules. |
| `mcp/legal_texts/manifest.py` | Planned source-family and source-limitation validation helpers. |
| `mcp/legal_texts/relationships.py` | Planned Phase 2 relationship validation target. |
| `mcp/legal_texts/sources.py` | Existing CELEX metadata pattern for EU sources. |
| `mcp/legal_texts/data/laws.v1.json` | Existing canonical IDs for BDSG/TDDDG and DSGVO targets. |
| `docs/features/source-provenance.md` | Current provenance docs that must distinguish third-party metadata from official legal text. |

## Implementation Steps

### Step 1: Add the scope graph policy decision record

- **What**: Add `docs/source-policies/dsgvo-scope-graph.md` or an equivalent repo policy record documenting robots/terms/licensing review, allowed use, fallback behavior, and the no-editorial-text rule.
- **Where**: New docs policy file; link later from Phase 13 docs.
- **Why**: No later relationship or neighbor-source phase should depend on unapproved third-party crawling.
- **Required fields**: Record `policy_id`, `source_url`, `reviewed_at`, `robots_result`, `terms_result`, `allowed_use` (`manual_seed_only`, `automated_metadata_allowed`, or `excluded`), `no_editorial_text=true`, reviewer note, and fallback seed-file path.
- **Considerations**: If crawl/reuse is not approved, the chosen path is the manually maintained fallback seed graph.

### Step 2: Add fallback seed graph data

- **What**: Add `mcp/legal_texts/data/privacy_scope_seed.v1.json` with metadata-only seed relationships for DSGVO articles, recitals, topics, BDSG, TDDDG, LDSG placeholders, AI Act CELEX `32024R1689`, and Data Act CELEX `32023R2854`.
- **Where**: New data file under `mcp/legal_texts/data/`.
- **Why**: Phase 7 needs bounded EU neighbor seeds and Phase 11 needs validated relationship metadata.
- **Schema contract**: The seed file must include `schema_version="privacy-scope-seed.v1"`, `policy_id`, `generated_at` or `maintained_at`, `source_basis`, and `relationships`. Each relationship must include `relationship_id`, Phase 2 `relationship_type`, `subject` (`law`/`norm`/`source_limitation`), `object` (`law`/`norm`/`source_limitation`), `source_basis` (`manual_seed`, `approved_metadata`, or `policy_excluded`), provenance, and optional topic tags that are metadata-only. LDSG entries that are not imported yet must point to state-law source records or limitations planned by Phase 8 rather than dangling strings.
- **Considerations**: Seed entries must contain relationship source/provenance and target IDs or source-limitation IDs; do not include copied explanatory/editorial text.

### Step 3: Validate seed graph and source limitations

- **What**: Add validation that checks relationship IDs, relationship types, source provenance, official targets, source-limitation targets, and policy-excluded third-party source records.
- **Where**: `mcp/legal_texts/relationships.py`; `mcp/tests/test_scope_graph_policy.py`; `mcp/tests/test_relationship_records.py`.
- **Why**: Acceptance requires approved seed/fallback entries to convert into package relationship records.
- **Considerations**: Target records that are not imported yet should point to explicit planned source records or source limitations rather than dangling strings.

### Step 4: Export package relationship records

- **What**: Add a transformation helper that converts approved seed/fallback graph entries into Phase 2 `relationships.json` records.
- **Where**: `mcp/legal_texts/relationships.py`.
- **Why**: Keeps relationship-generation logic reusable by Phase 7, state-law phases, and Phase 11 runtime APIs.
- **Considerations**: Relationship metadata must remain separate from legal text and from search index content.

## Testing Plan

Primary verify command: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_scope_graph_policy.py mcp/tests/test_relationship_records.py mcp/tests/test_generated_package.py`

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Policy | Approved, fallback, and policy-excluded modes are represented explicitly. | Validation rejects missing policy decisions. |
| Unit | Seed graph entries transform into package relationship records with valid targets or limitations. | Generated records pass relationship validation. |
| Unit | AI Act/Data Act CELEX seed records and LDSG placeholders have official-record or source-limitation targets. | Phase 7/state-law phases receive bounded, valid seed inputs. |
| Negative | Seed entries with editorial text, missing provenance, bad CELEX IDs, or dangling targets fail. | Tests report explicit validation errors. |

### Test Integrity Constraints

- Do not add scraped `dsgvo-gesetz.de` editorial text to fixtures or docs.
- Do not make Phase 7 depend on unapproved crawl output; use the seed graph file or source limitations.
- Existing package relationship tests from Phase 2 must remain valid.

## Rollback Strategy

Remove the policy record, seed graph data file, relationship transformation helpers, and related tests. Phase 7 would need manually supplied CELEX seeds until this phase is restored.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Third-party scope source use | Automated crawl; manually maintained fallback; policy exclusion only | Manually maintained fallback by default; automated crawl only after explicit terms/robots approval | This keeps Phase 6 executable without depending on unapproved third-party crawling or copied editorial text. |
| Minimum EU neighbor seeds | AI Act only; Data Act only; both | Both | Phase scope explicitly requires CELEX `32024R1689` and `32023R2854`. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/legal_texts/data/laws.v1.json` | Current registry data | Current registry has no relationship or topic metadata. |
| `mcp/legal_texts/sources.py` | `SourceSpec`, DSGVO metadata | Provides the CELEX/source metadata pattern to reuse for EU seeds. |
| `mcp/legal_texts/validation.py` | Planned relationship package validation from Phase 2 | Relationship records should validate before runtime APIs exist. |
| `docs/features/source-provenance.md` | Source metadata rules | Must distinguish official legal text provenance from third-party relationship-source provenance. |

### Mismatches / Notes

- There is currently no `relationships.json` runtime or data file; this relies on Phase 2.
- The implementation should default to the manually maintained fallback seed graph. Automated discovery can be added only after the policy record explicitly approves it.
