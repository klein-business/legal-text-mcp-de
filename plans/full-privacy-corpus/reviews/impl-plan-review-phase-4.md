---
type: review
entity: implementation-plan-review
plan: "full-privacy-corpus"
phase: 4
status: final
reviewer: "general"
created: "2026-05-15"
---

# Implementation Plan Review: Phase 4 - GII bulk normalization and coverage gates

> Reviewing [Phase 4 Implementation Plan](../implementation/phase-4-impl.md)
> Against [Phase 4 Scope](../phases/phase-4.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan is directionally aligned with Phase 4, but it leaves the highest-risk integration points underspecified: discovered GII records cannot currently flow through the static `LawRegistry`/`normalize_snapshot` path, terminal-state manifests are not tied to the planned manifest validator, and the verification command does not actually run the full-discovery coverage gate. An implementer would need to infer too much about generated registry creation, manifest shape, and live-gate evidence before this can be executed reliably.

## Scope Alignment

### Findings

- Scope is mostly correct: it stays on GII normalization, parser variants, source failures, fixture coverage, and BDSG/TDDDG gates. It does not drift into DSGVO, state-law, or relationship work.
- The plan does not fully cover the phase deliverable for a "parser-variant matrix documenting covered GII XML structures and examples"; it mentions fixture ZIPs/tests, but no documentation artifact or structured matrix file.
- Critical-law checks are in scope, but the implementation plan only says "imported-and-resolvable evidence or release-blocking upstream limitations" without defining where that evidence is persisted in the generated package or gate artifact.

## Technical Feasibility

### Findings

- **Major**: Full discovered GII items will not work through the current static registry path as written. `mcp/legal_texts/normalizer.py::normalize_snapshot` resolves every manifest entry with `LawRegistry.resolve_law(entry["canonical_id"])`, and `mcp/legal_texts/data/laws.v1.json` only contains the current fixture-sized set. A Phase 4 bulk manifest from Phase 3 will contain many source paths that are absent from the registry, so normalization would fail before parsing. The plan needs a concrete generated-registry step: derive law records from Phase 3 discovery metadata, preserve explicit migration/alias entries for existing IDs such as `tdddg` -> source path `ttdsg`, inject that registry into normalization, and validate collisions before writing laws/norms.
- **Major**: Terminal-state recording is not anchored to the Phase 1 manifest contract. The plan mentions `unsupported_format`, `source_unavailable`, and `parse_failed`, but it does not say to use `mcp/legal_texts/manifest.py::validate_corpus_manifest(..., require_terminal_states=True)` from the earlier phase plan, nor does it define how imported records, source limitations, generated record IDs, parser version, and diagnostics are represented. This risks adding an ad hoc import artifact that passes the new script but is incompatible with generated-package validation.
- **Major**: The plan assumes Phase 3 outputs but does not name or verify the concrete Phase 3 symbols/files that Phase 4 must consume. In the current repo, `mcp/legal_texts/gii_toc.py`, `mcp/legal_texts/manifest.py`, and `mcp/tests/test_corpus_manifest.py` do not exist yet. Since Phase 4 is blocked by Phase 3, that can be acceptable, but the Phase 4 implementation plan should explicitly list these as prerequisite artifacts and fail early if the discovery manifest schema is unavailable.
- **Minor**: Parser-variant behavior is too open-ended for `annex`, `section`, generic structural containers, repealed/empty norms, and title-only containers. Current `mcp/legal_texts/gii_xml.py::parse_gii_zip` only emits `par` and `art` units, with article-child paragraphs. The plan should specify the target `unit`, `norm_id`, `status`, URL pattern, `children`, and text/null handling for each new structural class so implementers do not invent incompatible mappings.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Add bulk GII normalization orchestration | Partial | Partial | Correct area, but it does not define the Phase 3 manifest schema, generated registry construction, or where terminal states are persisted. |
| 2 | Extend GII parser variant coverage | Partial | Partial | Names representative variants, but not expected normalized IDs/units/statuses or the required parser-variant matrix artifact. |
| 3 | Generate stable canonical IDs and provenance | Partial | No | The static registry cannot resolve full discovery entries. "registry.py or a generated registry helper" is not concrete enough for collision, alias, and migration behavior. |
| 4 | Add terminal-state and critical-law gates | Partial | Partial | A script path is named, but no CLI contract, artifact schema, manifest validator integration, or live/scheduled command is specified. |

## Required Context Assessment

### Missing Context

- `mcp/legal_texts/manifest.py` - planned Phase 1 terminal-state constants and `validate_corpus_manifest` are central to Phase 4 coverage gates.
- `mcp/legal_texts/gii_toc.py` - planned Phase 3 discovery records are the input to bulk normalization; the plan should name the concrete parser/discovery artifact interface once Phase 3 exists.
- `mcp/tests/test_corpus_manifest.py` and `mcp/tests/test_generated_package.py` - Phase 4 changes should preserve manifest and generated-package validation behavior from earlier phases.
- `mcp/legal_texts/models.py` - current `NormUnit` is only `par`/`art`; parser variant expansion depends on Phase 2's unit validation changes.
- `mcp/legal_texts/dataset.py` and `mcp/legal_texts/resolver.py` - critical-law "resolvable" evidence depends on the dataset/registry/resolver path, not only normalized JSON creation.

### Unnecessary Context

- None material.

## Testing Plan Assessment

### Test Integrity Check

The plan lists some existing tests that must remain valid, but it does not identify all validation tests affected by terminal-state/package work and does not explicitly state that existing tests will not be disabled or weakened. Most importantly, it does not include the manifest/generated-package tests expected from Phases 1 and 2, even though Phase 4 depends on those contracts.

### Test Gaps

- **Major**: The primary verify command does not execute `scripts/verify_gii_corpus_gate.py` or any live/full-discovery coverage command. A pytest-only command can validate fixtures, but it cannot satisfy the plan and Phase 4 acceptance criterion that a required explicit or scheduled full-discovery gate proves exactly one terminal state per discovered GII source.
- **Major**: The primary verify command omits manifest/package validation tests such as `mcp/tests/test_corpus_manifest.py` and `mcp/tests/test_generated_package.py` from earlier phase plans. Because Phase 4 writes terminal states and generated records, these tests are needed to catch incompatible manifest or package artifacts.
- **Minor**: BDSG/TDDDG tests are described at a high level but do not specify both required paths: successful import/resolution from GII provenance and release-blocking upstream limitation classification. The gate should have fixture cases for both, including rejecting ordinary `parse_failed` or `unsupported_format` as acceptable critical-law outcomes when the source is reachable.

### Real-World Testing

Real-world/integration testing is named in concept but not planned as an executable verification step. The plan should add a separate opt-in command for the network-heavy GII corpus gate, with an artifact output path, and keep the fixture pytest command as the fast CI gate.

## Reference Consistency

### Findings

- `mcp/legal_texts/gii_toc.py` is referenced indirectly through Phase 3 outputs, but the file does not exist in the current repo. The plan should mark it as a Phase 3 prerequisite artifact, not as current code.
- `scripts/verify_gii_corpus_gate.py` is a valid new path, but the plan does not define its command-line interface or expected artifact inputs/outputs.
- The Reality Check says current parser does not support "generic structural container units added in Phase 2"; in current code `mcp/legal_texts/models.py::NormUnit` is still only `par`/`art`. This is true only as a future Phase 2 assumption, not as current code reality.

## Reality Check Validation

### Findings

- **Major**: The Reality Check correctly notes that `normalize_snapshot` lacks per-entry failure handling, but it misses the more immediate blocker: `normalize_snapshot` requires every entry to resolve through the static `LawRegistry`, so most Phase 3 discovered GII entries will fail before parser handling or terminal-state classification.
- **Minor**: The Reality Check says `import_snapshot` raises on source failures, which is accurate for the current static `SOURCE_SPECS` importer, but Phase 4's bulk path should probably not be a direct extension of that function because it is tied to `SOURCE_SPECS.values()` rather than discovered GII source records.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Technical Feasibility | Full GII discovery entries cannot currently normalize through the static `LawRegistry` path. | Add a concrete generated-registry/migration step and make normalization consume it explicitly. |
| 2 | Major | Technical Feasibility | Terminal-state handling is not tied to the planned corpus manifest validator or generated-package contract. | Specify use of `validate_corpus_manifest(..., require_terminal_states=True)` and the exact artifact fields for imported/limited/failed states. |
| 3 | Major | Testing | The primary verify command does not run the full-discovery GII corpus gate. | Add a separate opt-in real-world gate command for `scripts/verify_gii_corpus_gate.py` with persisted artifact output. |
| 4 | Major | Testing | Manifest/generated-package validation tests are omitted despite Phase 4 depending on those contracts. | Include earlier-phase manifest/package validation tests in the primary or secondary verification path. |
| 5 | Minor | Step Quality | Parser variant outputs are underspecified for annexes, sections, containers, and empty/repealed norms. | Define expected `unit`, `norm_id`, `status`, URL, child, and text behavior for each variant. |
| 6 | Minor | Scope Alignment | The parser-variant matrix deliverable is not represented as an artifact. | Add a fixture-backed matrix file or documented table and test that it stays in sync with fixtures. |

## Recommendations

1. Revise Steps 1 and 3 to define generated GII law registry creation from Phase 3 discovery records, including alias/migration preservation for existing hand-authored IDs and collision validation before parsing.
2. Revise Steps 1 and 4 to use the Phase 1 manifest contract directly, including terminal-state field requirements and generated record references.
3. Add a real-world gate command for `scripts/verify_gii_corpus_gate.py` with explicit input discovery/import artifact paths and persisted output evidence.
4. Expand the primary verification path to include manifest/package validation tests from earlier phases, or add a named secondary command that must pass before Phase 4 is accepted.
5. Specify parser-variant expected outputs and add the missing parser-variant matrix deliverable.
