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

The updated plan closes the main structural gaps around German-law source paths, alias decisions, shared identifiers, error payloads, dataset readiness ownership, MCP migration, and phase boundaries. German `gesetze-im-internet.de` source rows were independently spot-checked and the valid/invalid path decisions for `ttdsg`/`tddsg` and `pangv_2022`/`pangv` match current source behavior. Execution is still materially at risk because DSGVO/EUR-Lex acquisition is not an executable dataset contract, the EGBGB `Art. 246a` fixture does not match the real source structure closely enough, production startup/container migration away from `bundestag/gesetze` has no clear phase owner, and search score determinism remains underspecified.

## Requirement Coverage

| Requirement | Covered By | Gap? | Notes |
| ----------- | ---------- | ---- | ----- |
| Replace productive `bundestag/gesetze` dependency with `gesetze-im-internet.de` German sources | Plan requirements, Phase 2, Phase 9 | Yes | Import replacement is covered, but runtime/container/default config migration is only verified at Phase 9 and has no implementation owner. |
| Reproducible import with raw snapshots, manifest, hashes, provenance, and stand date | Phases 1, 2, 4; `source-matrix.md` | Partial | German-law path/status validation is now concrete. DSGVO/EUR-Lex snapshot acquisition and accepted source artifact are not concrete. |
| Keep raw and normalized data separate | Phases 1, 2, 4 | No | The phase split is clear. |
| Supported Phase 1 law set and source matrix | `source-matrix.md`, `fixture-inventory.md`, Phases 1-3, 9 | Partial | German matrix rows are concrete; EGBGB `Art. 246a` and DSGVO need source-shape decisions before golden fixtures are executable. |
| Versioned alias registry and canonical identifiers | `contracts.md`, Phase 3 | No | Source path vs display code decisions are explicit. |
| Structured norm model and citation resolver | `contracts.md`, Phases 4-5 | Partial | Resolver grammar is clear, but the EGBGB `art:246a` fixture needs container-vs-child norm semantics. |
| Search contract with deterministic snippets, scores, and ordering | `contracts.md`, Phase 6 | Yes | Query/snippet/tie-break rules exist, but score meaning/range/formula is not pinned down. |
| Stable MCP tools returning JSON objects | `contracts.md`, Phase 7 | No | MCP migration decision and double-serialization regression are explicit. |
| HTTP API, OpenAPI, and shared structured errors | `contracts.md`, Phase 8 | No | Error grammar and HTTP/MCP mappings are sufficiently early and shared. |
| Shared dataset readiness across startup, MCP, HTTP, and tests | `contracts.md`, Phase 4, Phases 7-8 | Partial | Data-layer readiness owner is clear, but startup/runtime wiring to the new dataset package is not assigned before the release gate. |

## Scope Clarity

### Findings

- DSGVO is in scope as an EUR-Lex law, but the plan currently treats the EUR-Lex `TXT` URL's `202` response as a probe result instead of defining a retrievable source artifact. The official EUR-Lex machine-readable retrieval guidance points implementers toward XML notices and Cellar manifestations, while the matrix only stores `CELEX:32016R0679` plus a `TXT` page URL.
- The EGBGB `Art. 246a` fixture is too coarse. Current `gesetze-im-internet.de` XML exposes an `Art 246a` structural container with empty content and separate child entries such as `Art 246a § 1` with real text; the plan asks for golden JSON containing text for `Art. 246a` without saying whether the resolver should return the empty container, aggregate children, or require a child section citation.
- The plan declares `bundestag/gesetze` non-production, but the current repo's runtime defaults still load `/app/gesetze/` and the Dockerfile still clones `https://github.com/bundestag/gesetze.git`. The plan needs an implementation phase owner for replacing that startup path, not just a Phase 9 verification.

## Definition of Done Assessment

### Findings

- The DoD requires server startup from a validated Phase 1 dataset without `bundestag/gesetze`, but no phase acceptance criterion explicitly updates default settings, Docker packaging, or runtime startup to use the new validated dataset package.
- The DoD requires required fixture norms to resolve with URLs and provenance, but EGBGB `Art. 246a` and DSGVO do not yet have executable source/fixture semantics precise enough to produce stable golden JSON.

## Phase Structure Assessment

| Phase | Title | Verdict | Issue |
| ----- | ----- | ------- | ----- |
| 1 | Domain Contracts and Dataset Layout | Revise | Add explicit DSGVO source artifact policy and EGBGB container/child fixture semantics to the contracts produced here. |
| 2 | Reproducible Source Import | Revise | Own EUR-Lex/Cellar retrieval or explicitly mark DSGVO as a separate pre-snapshotted fixture source with acceptance criteria. |
| 3 | Canonical Registry and Alias Resolution | OK | Alias/source-path boundaries are clear. |
| 4 | Structured Normalization and Validation | Revise | Must know whether `art:246a` is a structural container, aggregate, or invalid without a child section. |
| 5 | Citation Resolver | Revise | Golden resolver tests for EGBGB `Art. 246a` are not executable until Phase 1/4 define expected semantics. |
| 6 | Search Index and Result Contract | Revise | Score determinism needs a concrete contract before fixture-backed expectations are written. |
| 7 | MCP Tool API Migration | Revise | MCP readiness can consume the shared state, but runtime startup must also stop depending on the legacy data path. |
| 8 | HTTP API and OpenAPI | OK | Thin HTTP layer and shared error mapping are well scoped. |
| 9 | Fixture Coverage, Docs, and Release Gate | OK | Correctly framed as a gate, but should not be the first owner for runtime data-source migration. |

## Testing Strategy Assessment

### Test Coverage Gaps

- DSGVO tests cannot become reliable golden/source tests until the plan defines the accepted EUR-Lex/Cellar source artifact, content type, language/version policy, and snapshot validation rule.
- EGBGB `Art. 246a` golden tests need exact expectations for an empty article container with child `§` entries; otherwise implementers may produce incompatible resolver behavior while still satisfying the broad fixture name.
- Search tests can assert ordering only after `score` is defined as a normalized API value, a backend-specific bounded value, or omitted from exact equality checks.
- Runtime tests should include startup/config/container behavior proving the server no longer defaults to the cloned Bundestag dataset.

### Real-World Testing

Real-world/source validation is present but incomplete. Independent probes on 2026-05-14 confirmed the German matrix's valid `index.html`/`xml.zip` rows return 200, `https://www.gesetze-im-internet.de/tddsg/index.html` returns 404, and `https://www.gesetze-im-internet.de/pangv/index.html` returns 404. The DSGVO row is weaker: `https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32016R0679` returns HTTP 202 with an HTML challenge response in this environment, while `http://publications.europa.eu/resource/celex/32016R0679` resolves to Cellar RDF; the plan should use an actually retrievable official artifact or explicitly document a pre-snapshot process.

## Reference Consistency

### Findings

- `contracts.md` uses `egbgb/art:246a` as a canonical citation example, and `fixture-inventory.md` requires `Art. 246a` as a golden fixture, but the real source has an empty `Art 246a` container plus child `§` entries. This is a contract/fixture/source mismatch, not just an implementation detail.
- `source-matrix.md` says import validation must probe each German law, but it does not impose an equivalent acceptance rule for the EUR-Lex row even though DSGVO is part of the required fixture set.

## Completeness Check

### Findings

- The plan is ready for German-law import/registry work after the noted fixes. It is not yet ready for the full Phase 1 law set because DSGVO and EGBGB fixture semantics would force implementers to make source-shape decisions during execution.
- The plan should move production data-source wiring out of the final release gate and into an earlier implementation phase, likely Phase 4 or Phase 7, with Phase 9 verifying rather than discovering it.

## Findings Summary

| # | Severity | Area | Finding | Recommendation |
| - | -------- | ---- | ------- | -------------- |
| 1 | Major | Source validation / dataset readiness | DSGVO/EUR-Lex is in the required law set, but the matrix only records a `TXT` URL that returns HTTP 202 here and Phase 2 validation only has concrete probe requirements for German laws. | Define the accepted DSGVO source artifact before implementation: EUR-Lex XML notice plus Cellar manifestation, another official machine-readable URL, or an explicit committed/pre-snapshot source process. Add content-type/status/hash/stand/version acceptance criteria and include it in dataset readiness. |
| 2 | Major | Fixture specificity / identifier contract | EGBGB `Art. 246a` is required as a golden fixture, but current official source structure exposes an empty `Art 246a` container and text-bearing child entries such as `Art 246a § 1`. | Decide whether `egbgb/art:246a` returns a structural container, aggregates child sections, or requires a more specific citation such as `Art. 246a § 1`. Update contracts, fixture inventory, URL expectations, and resolver tests accordingly. |
| 3 | Major | Phase boundaries / runtime migration | The plan removes productive `bundestag/gesetze` dependency in principle, but no phase owns changing the current Docker/default startup path that still loads `/app/gesetze/` from a cloned Bundestag repo. | Add an explicit Phase 4 or Phase 7 deliverable and acceptance criterion for runtime config/container startup from the validated dataset package, with Phase 9 only re-verifying absence of production Bundestag dependency. |
| 4 | Major | Search determinism | `contracts.md` defines query normalization, snippet rules, and tie-breaking, but does not define the `score` value even though Phase 6 and the API contract require returning scores. | Specify whether `score` is a normalized API score with a fixed range/formula, a backend score with bounded assertions, or a rank-only field. Make tests assert the chosen contract rather than raw backend behavior. |

## Recommendations

1. Fix the DSGVO source contract first; it affects source matrix correctness, dataset readiness, fixture generation, resolver tests, MCP, and HTTP.
2. Resolve the EGBGB `Art. 246a` container-vs-child fixture decision before Phase 4/5 planning.
3. Assign runtime/container/default dataset migration to an implementation phase before Phase 9.
4. Pin the search score contract in `contracts.md` before writing Phase 6 fixture expectations.
