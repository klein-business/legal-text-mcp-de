---
type: review
entity: implementation-plan-review
plan: "reliable-law-data-mcp"
phase: 3
status: final
reviewer: "general"
created: "2026-05-14"
---

# Implementation Plan Review: Phase 3 - Canonical Registry and Alias Resolution

> Reviewing [Phase 3 Implementation Plan](../implementation/phase-3-impl.md)
> Against [Phase 3 Scope](../phases/phase-3.md) and [Plan](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The plan is mostly executable and correctly keeps Phase 3 as a registry layer rather than a runtime MCP migration. However, it leaves two correctness-sensitive areas under-specified: full required-alias test coverage across the source matrix, and how ambiguity errors coexist with fail-fast collision validation. These should be tightened before execution because they affect the exact behaviors Phase 3 is meant to make auditable.

## Scope Alignment

Phase 3 scope is broadly aligned. The implementation plan adds a data-owned registry, loader, alias normalization, source-path separation, collision checks, suggestions, and documentation while explicitly deferring parser, MCP, HTTP, search, and citation integration.

### Findings

- **Major**: The testing plan does not explicitly require resolution tests for every alias in `source-matrix.md`. It names the headline acceptance examples for UWG, TDDDG, BDSG, PAngV, and DSGVO, but it does not force tests for all required BGB, EGBGB, DDG, BFSG, and VSBG aliases such as `BGBEG`, `bgbeg`, `Buergerliches Gesetzbuch`, `Digitale-Dienste-Gesetz`, `Barrierefreiheitsstaerkungsgesetz`, and `Verbraucherstreitbeilegungsgesetz`. Source-spec alignment may catch metadata drift, but Phase 3's core behavior is alias resolution, so every `Required Aliases` cell in `source-matrix.md` should be a table-driven resolver test.

## Technical Feasibility

The proposed module shape is feasible once Phase 2 has executed: `mcp/legal_texts/models.py`, `errors.py`, and `sources.py` are expected Phase 2 outputs, and Phase 3 can add `registry.py` and `mcp/legal_texts/data/laws.v1.json` without touching legacy runtime behavior in `mcp/parser.py`.

The plan correctly identifies current code anchors: `LawLibrary` stores laws by lowercased Markdown `jurabk`, `get_available_laws` uses `rapidfuzz` fuzzy matching, and `get`/`search` still construct URLs from lowercased display codes. That supports the decision to keep registry suggestions separate from legacy fuzzy lookup until later phases.

### Findings

- **Major**: Ambiguity behavior is not technically pinned down. The plan says alias collisions fail validation before runtime serving, but also requires `AMBIGUOUS_LAW_ALIAS` behavior via an intentionally bad in-memory registry. That leaves implementers guessing whether the resolver should ever operate on an invalid registry, whether there is a non-validating constructor for tests only, or whether ambiguity is reserved for future external registries. Tighten this by defining the exact API boundary, for example `validate_registry(...)` rejects collisions while a low-level `LawRegistry(..., validate=False)` may be used only to unit-test `AMBIGUOUS_LAW_ALIAS` serialization. Without that, the plan risks either dead ambiguity code or weakened startup validation.
- **Minor**: DSGVO registry source identity is still too loose. The plan says DSGVO uses "CELEX/Cellar identity according to the Phase 2 source spec", but the registry artifact fields only name `source_identifier`. To avoid inconsistent choices such as `CELEX:32016R0679`, Cellar work ID, source URL, or a compound string, the plan should state the exact DSGVO registry serialization and alignment assertion, including whether registry metadata mirrors `celex`, `cellar_work`, `expression`, and `language` or delegates those fields entirely to `sources.py`.

## Step Quality Assessment

| Step | Title | Concrete? | Actionable? | Issue |
| ---- | ----- | --------- | ----------- | ----- |
| 1 | Create Versioned Registry Artifact | Yes | Mostly | Should explicitly require every `source-matrix.md` required alias, not only examples. |
| 2 | Implement Registry Models and Loader | Yes | Yes | None. |
| 3 | Validate Source Alignment and Collisions | Mostly | Mostly | Needs a precise source of truth for DSGVO source identity and the exact source-spec alignment API. |
| 4 | Implement Alias Resolution and Suggestions | Mostly | Mostly | Ambiguous-alias behavior conflicts with fail-fast collision validation unless a test-only/low-level invalid registry path is specified. |
| 5 | Add Required Registry Tests | Mostly | Mostly | Does not explicitly require table-driven coverage for all source-matrix aliases. |
| 6 | Document Registry Boundary | Yes | Yes | Boundary is clear: registry exists, legacy runtime integration is deferred. |

## Required Context Assessment

### Missing Context

- `mcp/tests/fixtures/source_matrix_expected.json` should be listed if Phase 2 creates it as the independent oracle for source-matrix coverage. Phase 3 can then compare registry entries to Phase 2 source specs while `test_source_matrix.py` verifies those specs against the fixture/matrix.

### Unnecessary Context

- None found. The listed docs and legacy parser anchors are relevant because Phase 3 intentionally documents and preserves the runtime boundary.

## Testing Plan Assessment

### Test Integrity Check

The plan identifies that existing parser/library tests should remain unchanged because runtime integration is deferred, and it correctly adds new registry tests instead of changing legacy behavior. It also keeps collision tests in memory, so committed registry data does not need to be mutated during tests.

### Test Gaps

- Add table-driven tests asserting every alias from `source-matrix.md` resolves to the expected canonical ID, display code, source kind, and source identifier.
- Add an explicit test for `EGBGB`-style near misses or other unknown aliases only if suggestions are deterministic and bounded; do not rely on legacy `rapidfuzz` behavior from `LawLibrary.get_available_laws`.
- Add a test that the registry artifact's committed data is collision-free and that any ambiguous-error test uses a clearly documented low-level invalid registry construction path.

### Real-World Testing

No live or external real-world test is planned for Phase 3. That is acceptable for a static alias registry if Phase 2's source probes remain the upstream availability gate, but the plan should say this explicitly so Phase 3 completion is judged by deterministic registry/source-spec conformance rather than network checks.

## Reference Consistency

### Findings

- **Note**: The `mcp/legal_texts/*` paths are expected Phase 2 outputs and are not present in the current repository snapshot. This is not a Phase 3 finding by itself because Phase 3 is blocked by Phase 2; implementation should simply verify those modules exist before beginning Phase 3.

## Reality Check Validation

The Reality Check accurately describes the current legacy runtime: `mcp/parser.py` keys loaded laws by lowercased `jurabk`, `LawLibrary.get_available_laws` uses fuzzy matching over loaded law keys, and `LawLibrary.get`/`search` build `gesetze-im-internet.de` URLs from lowercased law abbreviations. The plan correctly avoids claiming MCP tools use the registry before Phase 7.

### Findings

- **Minor**: The Reality Check should also mention that the current repo has no `mcp/legal_texts` package until Phase 2 executes. This avoids confusing Phase 3 implementers who start from a clean checkout before prior phases have been applied.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Alias coverage | The tests do not explicitly require every alias from `source-matrix.md` to resolve correctly. | Make registry tests table-driven from the full required alias set for all Phase 1 laws. |
| 2 | Major | Ambiguity semantics | The plan does not define how `AMBIGUOUS_LAW_ALIAS` can be exercised while collisions also fail validation before serving. | Define the low-level/test-only invalid registry path or otherwise clarify when ambiguity errors are reachable. |
| 3 | Minor | Source alignment | DSGVO `source_identifier` serialization is under-specified. | Pin the exact registry representation and assert it against Phase 2 source specs. |
| 4 | Minor | Reality check | The plan does not state that `mcp/legal_texts` is a prior-phase output absent from the current repo snapshot. | Add a prerequisite note so this is not misread as a current-code anchor. |
| 5 | Note | Real-world testing | Phase 3 has no live test, which is reasonable for static registry data but should be explicit. | State that Phase 3 relies on deterministic conformance tests and Phase 2 live source probes for upstream availability. |

## Recommendations

1. Revise Step 5 and the testing table so every `source-matrix.md` required alias is tested for canonical ID, display code, source kind, and source identifier.
2. Define the exact ambiguity/collision API boundary before implementation.
3. Pin DSGVO registry serialization against the Phase 2 source spec.
4. Add the Phase 2 source-matrix fixture to Required Context if it exists after Phase 2 execution.
