---
type: planning
entity: todo
plan: "full-privacy-corpus"
updated: "2026-05-15"
---

# Todo: full-privacy-corpus

> Tracking [full-privacy-corpus](plan.md)

## Plan Completed

### Phase Context

- **Scope**: [Phase 13](phases/phase-13.md)
- **Implementation**: [Phase 13 Plan](implementation/phase-13-impl.md)
- **Latest Handover**: none
- **Relevant Docs**:
  - [Design Spec](../../docs/superpowers/specs/2026-05-15-full-privacy-corpus-design.md)
  - [Root README](../../README.md)
  - [Project Overview](../../docs/overview.md)
  - [MCP Server Module](../../docs/modules/mcp-server.md)
  - [Law Loading and Indexing](../../docs/features/law-loading-and-indexing.md)
  - [Source Provenance](../../docs/features/source-provenance.md)
  - [Supported Laws](../../docs/features/supported-laws.md)
  - [Scope and Invariants](../../docs/features/known-issues.md)

### Pending

No tasks pending.

### In Progress

No tasks in progress.

### Completed

- [x] Authored Phase 1-13 implementation plans. <!-- completed: 2026-05-15 -->
- [x] Reviewed Phase 1-13 implementation plans to zero Critical, Major, Minor, and Note findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 1 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 2 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 3 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 4 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 5 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 6 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 7 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 8 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 9 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Validated Phase 8 inventory inputs and derived eligible stable-HTML states. <!-- completed: 2026-05-15 -->
- [x] Added state-law adapter result interfaces and HTML extraction helpers. <!-- completed: 2026-05-15 -->
- [x] Converted adapter results into generated package and manifest outcomes. <!-- completed: 2026-05-15 -->
- [x] Added representative state-law fixtures and package validation tests. <!-- completed: 2026-05-15 -->
- [x] Added opt-in state-law adapter gate evidence. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 10 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Verified prerequisite artifacts from Phases 1, 2, 8, and 9. <!-- completed: 2026-05-15 -->
- [x] Added final state-law coverage helper and summary artifact. <!-- completed: 2026-05-15 -->
- [x] Skipped PDF extraction because current inventory has zero PDF adapter-class records. <!-- completed: 2026-05-15 -->
- [x] Emitted explicit source limitations for unsupported remaining states. <!-- completed: 2026-05-15 -->
- [x] Added coverage, PDF/limitation, and opt-in source evidence tests. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 11 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Loaded generated package coverage, source limitations, and relationships in the dataset. <!-- completed: 2026-05-15 -->
- [x] Added runtime methods for corpus coverage, source limitations, and related norms. <!-- completed: 2026-05-15 -->
- [x] Added additive MCP tools for coverage, limitations, and related norms. <!-- completed: 2026-05-15 -->
- [x] Added HTTP endpoints and OpenAPI models for coverage, limitations, and relationships. <!-- completed: 2026-05-15 -->
- [x] Added resolver/API coverage for new citation units. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 12 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Added corpus runtime benchmark helper and deterministic larger fixture/generator. <!-- completed: 2026-05-15 -->
- [x] Added explicit full-corpus validation bundle gate script. <!-- completed: 2026-05-15 -->
- [x] Validated generated production dataset exclusions and artifact handling. <!-- completed: 2026-05-15 -->
- [x] Added package/search migration decision fields for missed budgets. <!-- completed: 2026-05-15 -->
- [x] Kept PR/release CI fixture-backed and network-free by default. <!-- completed: 2026-05-15 -->
- [x] Completed Phase 13 implementation and implementation review to zero findings. <!-- completed: 2026-05-15 -->
- [x] Updated root README with fixture-vs-production corpus guidance. <!-- completed: 2026-05-15 -->
- [x] Updated overview, feature, and module docs for full privacy corpus behavior. <!-- completed: 2026-05-15 -->
- [x] Added Mermaid architecture and sequence diagrams for corpus flow, release gates, and MCP/API lookup. <!-- completed: 2026-05-15 -->
- [x] Added docs link/image checks for README, docs, docs-legacy, and plans. <!-- completed: 2026-05-15 -->
- [x] Extended stale workflow checks to docs-legacy and plan artifacts while excluding quoted review evidence. <!-- completed: 2026-05-15 -->
- [x] Ran final release-readiness verification after docs updates. <!-- completed: 2026-05-15 -->
- [x] Completed full-privacy-corpus plan with all 13 phases reviewed to zero findings. <!-- completed: 2026-05-15 -->

### Blocked

No tasks blocked.

## Changelog

### 2026-05-15

- Plan created from `docs/superpowers/specs/2026-05-15-full-privacy-corpus-design.md`.
- Plan review findings addressed: tightened full-corpus gates, canonical ID
  policy, provenance matrix, terminal-state taxonomy, EU seed policy, state-law
  phase split, negative tests, and docs-check ownership.
- Second plan review findings addressed: relationship package ownership,
  DSGVO/EUR-Lex version policy, and full-corpus validation evidence bundle.
- Third plan review finding addressed: BDSG/TDDDG named-law import and runtime
  evidence gate.
- Implementation planning completed for all 13 phases: implementation plans
  were authored, reviewed, revised, and re-reviewed to zero findings.
- Started Phase 1 execution: Manifest and corpus contract foundation.
- Completed Phase 1 after rework and independent implementation review:
  manifest contract, validation fixtures, release-gate integration, and
  source-provenance docs are in place.
- Started Phase 2 execution: Generated package format and runtime compatibility.
- Completed Phase 2 after rework and independent implementation review:
  generated package validation, fixtures, release-gate integration,
  package/provenance docs, and JSON-path robustness are in place.
- Started Phase 3 execution: Complete GII discovery coverage.
- Completed Phase 3 after rework and independent implementation review:
  discovery artifact schema, fixture tests, opt-in live gate, and coverage docs
  are in place.
- Started Phase 4 execution: GII bulk normalization and coverage gates.
- Completed Phase 4 after rework and independent implementation review:
  fixture-backed GII bulk package generation, terminal-state coverage,
  parser-variant matrix, critical-law gates, and docs are in place.
- Started Phase 5 execution: Full DSGVO articles and recitals.
- Completed Phase 5 after rework and independent implementation review:
  official DSGVO Cellar/Formex `<CONSID>` recitals, article/recital resolver
  coverage, source policy, count gate, and docs are in place.
- Started Phase 6 execution: DSGVO scope policy and seed graph inventory.
- Completed Phase 6 after independent implementation review: metadata-only
  scope policy, fallback seed graph, AI Act/Data Act CELEX limitations,
  relationship transformation helpers, and release-gate tests are in place.
- Started Phase 7 execution: EU neighbor acts source family.
- Completed Phase 7 after rework and independent implementation review:
  official Cellar DOC_1 FMX4 ZIP provenance, AI Act/Data Act parser support,
  source limitation handling, opt-in evidence gate, relationship target
  readiness, and docs are in place.
- Started Phase 8 execution: German state-law source family inventory.
- Completed Phase 8 after reachability rework and independent implementation
  review: all 16 states have explicit inventory outcomes, current reachability
  evidence has no unresolved mismatches, and state-law inventory docs/tests are
  in place.
- Started Phase 9 execution: German state-law machine-readable and HTML
  adapters.
- Completed Phase 9 after portal-chrome rework and independent implementation
  review: BB and NRW stable HTML imports are clean, remaining eligible states
  have explicit limitations, generated package validation and release gates
  pass, and Phase 10 started.
- Completed Phase 10 after coverage validation hardening and independent
  implementation review: all 16 state-law outcomes are imported or explicitly
  limited, zero PDF sources are claimed in the current inventory, no manual text
  is introduced, and Phase 11 started.
- Completed Phase 11 after generated-package E2E and resolver-contract
  hardening: coverage, source limitation, and relationship APIs are available
  over runtime/MCP/HTTP, legacy and generated-package E2E pass, and Phase 12
  started.
- Completed Phase 12 after operational-gate hardening and independent review:
  release verification is network-free by default, full-corpus bundle evidence
  validates required source-family outcomes and critical-law resolution, and
  Phase 13 started.
- Completed Phase 13 after documentation/release-readiness hardening and
  independent review: root README, overview, module docs, feature docs,
  diagrams, docs link/image checks, stale workflow checks, and release gate
  verification are complete with zero remaining findings.
- Plan completed: all 13 phases have accepted implementation reviews with zero
  remaining findings.
