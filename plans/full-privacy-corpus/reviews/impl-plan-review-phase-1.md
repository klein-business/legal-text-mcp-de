---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 1
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 1 - Manifest and corpus contract foundation

> Reviewing [Phase 1 Implementation Plan](../implementation/phase-1-impl.md)
> Against [Phase 1 Scope](../phases/phase-1.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The implementation plan is directionally feasible and matches the current codebase layout: the existing normalized dataset validation is record-focused, `SourceKind` is limited to GII/EUR-Lex serving records, and adding an isolated `mcp/legal_texts/manifest.py` is a low-risk Phase 1 approach. It still needs revision because the steps and tests do not fully cover Phase 1's required versioned manifest/package contract, all terminal-state examples, or the release-gate acceptance criterion.

## Scope Alignment

### Findings

- **Major**: Phase 1 explicitly includes a corpus manifest schema for discovered sources, terminal states, hashes, retrieval timestamps, parser versions, source limitations, and generated package metadata, plus a versioned manifest contract. The implementation plan's Step 1 and Step 2 focus on source-family constants and per-source validation, but do not define top-level manifest fields such as manifest version, dataset/package identifiers, created/retrieved timestamps, validation mode, discovered-source collection shape, or generated package metadata. Without those fields, later phases can still invent incompatible manifest envelopes while passing the proposed source-record tests.
- **Major**: Phase 1 requires failure taxonomy examples for every terminal-state class. Step 4 only names fixtures for imported GII, imported EUR-Lex, one state-law limitation, one third-party policy exclusion, and one invalid duplicate/missing-provenance case. That does not clearly cover `unsupported_format`, `source_unavailable`, and `parse_failed`, nor does it require tests for their distinct required fields from the plan's failure taxonomy.

## Technical Feasibility

### Findings

- The proposed file locations are real and technically sound. `mcp/legal_texts/models.py` currently defines `SourceKind = Literal["gesetze-im-internet", "eur-lex-cellar"]` and `NormUnit = Literal["par", "art"]`; `mcp/legal_texts/validation.py` validates normalized law/norm source metadata only; `mcp/legal_texts/importer.py` writes a raw snapshot `manifest.json` over static `SOURCE_SPECS`; and `mcp/legal_texts/sources.py` is fixture-sized. Keeping a broader generated-corpus manifest vocabulary separate from serving records in Phase 1 is feasible.
- **Minor**: Step 3 is underspecified for canonical ID and alias policy validation. It says to add "helpers or validation sections" for deterministic law IDs, alias migrations, duplicate canonical IDs, and collisions, but does not name the manifest sections, required fields, or negative test cases. This is risky because `mcp/legal_texts/registry.py` only validates current serving registry alias collisions; it does not validate generated GII source-path IDs, CELEX mismatches, state-law jurisdiction prefixes, relationship IDs, or migration entries.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Introduce the corpus manifest model | Partly | Partly | Real path and source-family constants are clear, but the top-level versioned manifest/package schema is not specified. |
| 2 | Add manifest validation rules | Partly | Partly | Per-source validation is clear; top-level manifest validation and package metadata validation are missing. |
| 3 | Define canonical ID and alias policy checks | Partly | Partly | References the real `LawRegistry`, but lacks concrete schema fields and required positive/negative cases. |
| 4 | Add representative manifest fixtures | Partly | Partly | Real fixture path is clear, but examples do not cover every terminal state required by Phase 1. |
| 5 | Add contract tests and documentation note | Yes | Partly | Test file and docs path are real; testing scope omits full terminal-state and release-gate coverage. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/dataset.py` - Shows `NormalizedDataset.load()` calls `validate_dataset_package`, `validate_laws`, and `validate_norms`; this supports the plan's decision not to wire manifest validation into runtime yet and helps avoid accidental startup behavior changes.
- `mcp/tests/test_registry.py` - Existing alias and historical source-path behavior are relevant to Step 3's canonical ID and alias policy work.

## Testing Plan Assessment

### Test Integrity Check

The implementation plan identifies `mcp/tests/test_dataset_validation.py` as the existing regression surface and states that it must remain semantically unchanged except for additive assertions. It also says normalized fixtures must not be edited merely to satisfy manifest tests and new manifest tests must use explicit invalid fixtures. That is adequate for test integrity; it does not propose disabling or weakening existing tests.

### Test Gaps

- **Major**: The primary verify command, `PYTHONPATH=mcp uv run --group dev pytest mcp/tests/test_corpus_manifest.py mcp/tests/test_dataset_validation.py`, does not prove the Phase 1 acceptance criterion that the existing fixture dataset still "passes release gates." The actual release gate is `scripts/verify_release.py`, which runs many additional test modules and `scripts/verify_e2e.py`. If the plan wants a shorter primary command, it should still add an explicit release-gate verification step or revise the acceptance evidence.
- **Major**: Tests are not required for each terminal state. The plan should add positive and negative cases for `imported`, `unsupported_format`, `source_unavailable`, `parse_failed`, and `excluded_by_policy`, including each state's required fields from `plan.md`.
- **Minor**: Canonical ID and alias policy tests are not concrete enough. The plan should require duplicate canonical ID rejection, duplicate discovered-source rejection, CELEX/canonical mismatch rejection, state-law ID without jurisdiction rejection, and relationship-source records not creating legal-text law IDs.

### Real-World Testing

No real-world/network testing is planned for Phase 1, which is acceptable for a fixture-only manifest-contract foundation because full GII discovery and live corpus gates are explicitly deferred to later phases. The review risk is not absence of live network access; it is that the fixture tests must fully exercise the contract that later live gates will depend on.

## Reference Consistency

### Findings

- The code anchors are accurate. `mcp/legal_texts/models.py`, `validation.py`, `importer.py`, `sources.py`, `registry.py`, and `mcp/tests/test_dataset_validation.py` exist and contain the symbols/areas described in the Reality Check.
- The affected module reference `docs/modules/mcp-server.md` exists. The required docs paths `docs/features/source-provenance.md` and `docs/features/law-loading-and-indexing.md` also exist and match the described provenance and package-loading context.

## Reality Check Validation

### Findings

- The Reality Check is mostly accurate: current serving `SourceKind` does not include state-law or third-party families; current raw snapshot manifests are static `SOURCE_SPECS` downloads; and validation is normalized-record focused. The missing Reality Check item is the top-level package contract gap: current `validate_dataset_package` only checks `laws.json`, `norms.json`, and optionally `search-index.json`, so Phase 1 must be explicit that the new corpus manifest envelope/version/package metadata is a separate contract until Phase 2 wires it into generated packages.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Scope / schema | The implementation plan does not define the top-level versioned manifest/package metadata contract required by Phase 1. | Add concrete manifest envelope fields and validation/tests for manifest version, package/dataset metadata, discovered-source collection shape, timestamps, validation mode, and generated package metadata. |
| 2 | Major | Scope / fixtures | Terminal-state examples and tests do not cover every required terminal state. | Require fixtures and tests for `imported`, `unsupported_format`, `source_unavailable`, `parse_failed`, and `excluded_by_policy`, with state-specific required fields. |
| 3 | Major | Testing | The primary verify command does not prove the acceptance criterion that fixture data still passes release gates. | Add `PYTHONPATH=mcp uv run --group dev python scripts/verify_release.py` as explicit release-gate evidence, or define why a smaller command is sufficient and adjust acceptance wording. |
| 4 | Minor | ID policy | Canonical ID, alias, collision, and migration checks are too vague to execute consistently. | Specify manifest sections and positive/negative tests for GII source-path IDs, CELEX IDs, state-law jurisdiction prefixes, relationship IDs, duplicate canonical IDs, and alias migrations. |

## Recommendations

1. Revise Steps 1-2 to define and validate the full manifest envelope, not only individual source records.
2. Expand Step 4 and the testing table so every terminal state has at least one representative fixture and at least one missing-required-field rejection test.
3. Add release-gate verification to the testing plan because Phase 1 acceptance explicitly requires it.
4. Make Step 3 executable by naming the canonical ID and alias policy fields and the exact invalid cases that must fail validation.
