---
type: review
entity: plan-review
plan: "reliable-law-data-mcp"
status: final
reviewer: "general"
created: "2026-05-14"
---

# Plan Review: reliable-law-data-mcp

> Reviewing [reliable-law-data-mcp](../plan.md)

## Overall Assessment

**Verdict**: Needs Revision

The updated plan is executable enough for the DSGVO Cellar source artifact, runtime migration away from `bundestag/gesetze`, and deterministic search score contract at Critical/Major severity. One Major gap remains: EGBGB `Art. 246a § 1` is defined as a child citation, but the resolver and HTTP request grammars still only clearly model a single norm level.

## Requirement Coverage

| Requirement | Covered By | Gap? | Notes |
| ----------- | ---------- | ---- | ----- |
| DSGVO must use a retrievable official non-`gesetze-im-internet` source artifact. | [source-matrix.md](../source-matrix.md), [phase-1.md](../phases/phase-1.md), [phase-2.md](../phases/phase-2.md), [phase-4.md](../phases/phase-4.md) | No Critical/Major gap | The Cellar XML URL, CELEX/work/expression/language metadata, content-type validation, hash, and separate `eur-lex-cellar` source kind are concrete enough. |
| EGBGB `Art. 246a` container and `Art. 246a § 1` child semantics must be executable. | [contracts.md](../contracts.md), [fixture-inventory.md](../fixture-inventory.md), [phase-4.md](../phases/phase-4.md), [phase-5.md](../phases/phase-5.md) | Major | Container/child semantics are defined, but structured caller input and HTTP path encoding for the child citation remain ambiguous. |
| Runtime must migrate away from `bundestag/gesetze`. | [phase-7.md](../phases/phase-7.md), [phase-9.md](../phases/phase-9.md), [contracts.md](../contracts.md) | No Critical/Major gap | Phase 7 owns runtime defaults and Docker packaging; Phase 9 re-verifies the migration. |
| Search score determinism must be independent of raw backend score exposure. | [contracts.md](../contracts.md), [phase-6.md](../phases/phase-6.md) | No Critical/Major gap | The public score range, top-hit normalization, fallback rank formula requirement, tie-break ordering, snippet rules, and fixture-backed tests are sufficiently actionable. |

## Scope Clarity

### Findings

- **Major**: EGBGB article-plus-section citations are specified as `egbgb/art:246a/par:1`, but the public resolver signature remains `resolve_citation(code, unit, paragraph_or_article, absatz?, satz?, nummer?, buchstabe?)`. The citation request rules allow only one `unit` and one `paragraph_or_article`, so a structured caller has no unambiguous place to put the child `§ 1` without overloading `absatz` or passing a composite string that the grammar does not define.

## Definition of Done Assessment

### Findings

- **Major**: The DoD requires fixture citations to resolve through service, MCP, and HTTP surfaces, but the plan does not yet define the exact wire shape for `EGBGB Art. 246a § 1`. This makes the EGBGB golden fixture objectively harder to implement and verify across transports.

## Phase Structure Assessment

| Phase | Title | Verdict | Issue |
| ----- | ----- | ------- | ----- |
| 1 | Domain Contracts and Dataset Layout | Needs revision | Must pin the article-plus-section request grammar, not only the canonical child ID. |
| 2 | Reproducible Source Import | OK | No remaining Critical/Major issue found in the focused review. |
| 3 | Canonical Registry and Alias Resolution | OK | No remaining Critical/Major issue found in the focused review. |
| 4 | Structured Normalization and Validation | OK with dependency | Normalization semantics are clear once Phase 1 pins the child norm/request grammar. |
| 5 | Citation Resolver | Needs revision | The resolver signature does not explicitly represent `Art. 246a § 1`. |
| 6 | Search Index and Result Contract | OK | No remaining Critical/Major issue found in the focused review. |
| 7 | MCP Tool API Migration | OK | No remaining Critical/Major issue found in the focused review. |
| 8 | HTTP API and OpenAPI | Needs revision | `/laws/{code}/norms/{norm}` examples do not define whether `art:246a/par:1` is a URL-encoded single segment, a nested route, or another accepted grammar. |
| 9 | Fixture Coverage, Docs, and Release Gate | OK with dependency | Release verification is adequate once the EGBGB child citation wire contract is pinned earlier. |

## Testing Strategy Assessment

### Test Coverage Gaps

- **Major**: Fixture inventory requires EGBGB container and child coverage, but the plan does not yet require a specific structured input test for `resolve_citation(EGBGB, Art. 246a § 1)` or a specific HTTP request path test for the same child citation.

### Real-World Testing

Real-world/source integration testing is planned: Phase 2 probes every source matrix row, validates the DSGVO Cellar XML artifact, and records manifests/hashes; Phase 9 re-verifies source probes and the full transport regression suite. No Critical/Major real-world testing gap remains outside the EGBGB child citation wire-contract issue.

## Completeness Check

### Findings

- **Major**: The plan defines the internal EGBGB child citation ID but not the API grammar that accepts or returns it consistently as a resolver request, MCP parameter set, and HTTP norm path.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | EGBGB citation contract | `Art. 246a § 1` has defined container/child semantics, but the resolver signature and HTTP norm path grammar still do not unambiguously carry the child `§` level. | Add an explicit article-plus-section request grammar before implementation, such as `child_unit`/`child_value` fields or a formally accepted composite norm grammar, then pin MCP and HTTP examples plus golden tests for `egbgb/art:246a/par:1`. |

## Recommendations

1. Update [contracts.md](../contracts.md) and Phase 5 to define exactly how structured resolver callers pass article-plus-section citations.
2. Update Phase 8 to define the exact HTTP path form for `art:246a/par:1`, including whether slash is encoded as one path segment or modeled as a nested route.
3. Add explicit golden tests for the service, MCP, and HTTP wire forms of both `EGBGB Art. 246a` and `EGBGB Art. 246a § 1`.
