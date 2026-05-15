---
type: review
entity: implementation-review
plan: "full-privacy-corpus"
phase: 6
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Review: Phase 6 - DSGVO scope policy and seed graph inventory

> Reviewing implementation of [Phase 6](../phases/phase-6.md)
> Against [Implementation Plan](../implementation/phase-6-impl.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Accepted

The implementation satisfies the Phase 6 acceptance criteria. It establishes a metadata-only manual seed policy for the `dsgvo-gesetz.de` scope reference, provides AI Act/Data Act CELEX-backed source limitations, validates that seed targets resolve to declared official targets or source limitations, and converts seed entries into the existing Phase 2 `relationships.json` package contract rather than introducing a competing schema.

## Acceptance Criteria Verification

| # | Criterion | Met? | Evidence | Gap |
| - | --------- | ---- | -------- | --- |
| 1 | Implementation has a permitted discovery path or an explicit fallback seed graph before relationship work proceeds. | Yes | `mcp/legal_texts/data/dsgvo_scope_policy.v1.json` sets `allowed_use` to `manual_seed_only`, requires `no_editorial_text_copied`, and points to `mcp/legal_texts/data/privacy_scope_seed.v1.json`. `validate_scope_policy()` enforces allowed-use values and fallback seed path requirements. | None. |
| 2 | AI Act and Data Act have concrete CELEX identifiers or source limitations. | Yes | `privacy_scope_seed.v1.json` includes `lim-eu-ai-act-32024r1689` with CELEX `32024R1689` and `lim-eu-data-act-32023r2854` with CELEX `32023R2854`. `MINIMUM_EU_NEIGHBOR_CELEXS` and `validate_privacy_scope_seed()` require both CELEX values. | None. |
| 3 | No phase depends on unapproved third-party crawling or copied editorial text. | Yes | Policy data records `manual_seed_only`; `validate_privacy_scope_seed()` rejects `approved_metadata` unless policy allows `automated_metadata_allowed`; recursive copied/editorial text field rejection is present in `relationships.py` and package relationship validation in `validation.py`. Repository search found only source/policy references and tests that inject forbidden fields, not copied third-party content. | None. |
| 4 | Approved seed/fallback graph entries can be converted into package relationship records whose targets are official records or source limitations. | Yes | `seed_relationships_to_package_records()`, `seed_limitations_to_package_records()`, and `seed_relationship_source_to_manifest_record()` produce Phase 2-shaped records. `test_transformed_seed_records_pass_generated_package_relationship_validation` builds a package with the transformed records and `validate_generated_package(..., require_search_index=True)` returns no errors. | None. |

## Plan Adherence

| Step | Planned | Actual | Deviation? | Assessment |
| ---- | ------- | ------ | ---------- | ---------- |
| 1 | Add scope graph policy decision record with robots/terms/licensing decision, allowed use, fallback behavior, and no-editorial-text rule. | Added `dsgvo_scope_policy.v1.json`; `validate_scope_policy()` checks schema version, required fields, HTTPS source URL, allowed use, fallback path, and copied/editorial text fields. | Location differs from suggested docs path, but the plan allowed an equivalent policy record. | Acceptable. The policy is machine-validated and directly consumed by tests. |
| 2 | Add fallback seed graph data for DSGVO, BDSG, TDDDG, LDSG placeholders, AI Act, and Data Act. | Added `privacy_scope_seed.v1.json` with DSGVO article/recital targets, BDSG/TDDDG official law targets, AI Act/Data Act EUR-Lex limitations, and a state-law limitation placeholder. | No problematic deviation. | Acceptable for Phase 6; later phases own full EU/state-law imports. |
| 3 | Validate seed graph and source limitations. | Added validation for policy/seed required fields, relationship source metadata, official targets, source limitations, relationship types, provenance, duplicate IDs, CELEX presence, and endpoint resolution. | None. | Matches plan. |
| 4 | Export package relationship records. | Transformation helpers create records with `relationship_id`, `relationship_type`, `subject`, `object`, `source_family`, `source_id`, `provenance`, and `metadata`, matching Phase 2 package validation. | None. | Matches plan. |

## Code Quality Assessment

### Findings

- No functional code quality findings. The implementation keeps Phase 6 logic in `mcp/legal_texts/relationships.py`, reuses the existing `RELATIONSHIP_TYPES`, `RELATIONSHIP_ENDPOINT_KINDS`, and generated package validator, and avoids broad runtime/API changes outside the phase scope.

## Testing Assessment

### Verify Command Result

- **Command**: `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_scope_graph_policy.py mcp/tests/test_relationship_records.py mcp/tests/test_generated_package.py`
- **Exit Code**: 0
- **Result**: 50 passed

- **Command**: `SKIP_LIVE_SOURCE_MATRIX=true PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py`
- **Exit Code**: 0
- **Result**: 142 passed; HTTP CLI E2E OK; MCP streamable HTTP E2E OK

### Test Quality

| Test | What it Tests | Meaningful? | Issue |
| ---- | ------------- | ----------- | ----- |
| `test_scope_policy_record_is_metadata_only_and_points_to_fallback_seed` | Policy mode, no-editorial-text flag, and fallback seed path. | Yes | None. |
| `test_seed_graph_rejects_automated_scope_without_policy_approval` | Prevents unapproved automated metadata/crawl dependency. | Yes | None. |
| `test_scope_policy_rejects_recursive_copied_editorial_text_fields` and `test_seed_graph_rejects_recursive_copied_editorial_text_fields` | Reject copied/editorial text fields recursively in policy and seed data. | Yes | None. |
| `test_seed_graph_rejects_dangling_state_law_placeholder` | Rejects dangling generic state-law/LDSG placeholders. | Yes | None. |
| `test_seed_graph_rejects_missing_minimum_eu_neighbor_celex` | Fails when required AI Act/Data Act CELEX seed coverage is missing. | Yes | None. |
| `test_seed_graph_rejects_unsupported_relationship_type` and `test_seed_graph_rejects_missing_relationship_provenance` | Rejects bad relationship types and missing provenance. | Yes | None. |
| `test_transformed_seed_records_pass_generated_package_relationship_validation` | Verifies generated seed records satisfy the Phase 2 generated package contract with resolving official targets/source limitations. | Yes | None. |
| Existing `test_generated_package.py` relationship/source limitation negatives | Covers unresolved relationship targets, undeclared relationship sources, copied text, unsupported endpoint kinds, duplicate IDs, unsupported relationship types, and source limitation manifest mismatch. | Yes | None. |

### Real-World Testing

Not performed for live `dsgvo-gesetz.de` discovery, and that is appropriate for this phase because the policy explicitly chooses the manual fallback seed path and does not approve crawling. Release verification was fixture-backed with `SKIP_LIVE_SOURCE_MATRIX=true`; the remaining real-world risk is intentionally deferred to later explicit/scheduled corpus gates.

## Scope Compliance

### Findings

- No scope findings. The implementation does not import EU neighbor full text, state-law full text, or runtime relationship lookup APIs, and it does not copy third-party editorial content.

## Regression Risk

### Test Integrity Check

- [x] No existing tests were found to be deleted.
- [x] No existing tests were found to be disabled.
- [x] No existing assertions were found to be weakened.
- [x] The release verification command passed with the live source matrix intentionally skipped.

### Findings

- No regression findings. The relationship conversion path is additive and is validated through the existing generated package validator.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| - | - | - | No findings. | No action required. |

## Recommendations

1. Accept Phase 6.
