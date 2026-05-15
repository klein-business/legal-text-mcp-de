---
type: planning
entity: phase
plan: "full-privacy-corpus"
phase: 1
status: pending
created: "2026-05-15"
updated: "2026-05-15"
---

# Phase 1: Manifest and corpus contract foundation

> Part of [full-privacy-corpus](../plan.md)

## Objective

Define the shared corpus manifest, source-family, terminal-state, and provenance
contract that every later source adapter and runtime feature will use.

## Scope

### Includes

- Corpus manifest schema for discovered sources, terminal states, hashes,
  retrieval timestamps, parser versions, source limitations, and generated
  package metadata.
- Source-family identifiers for GII, EUR-Lex/Cellar, state law, and third-party
  scope references.
- Terminal-state definitions for imported, unavailable, unsupported, failed, and
  policy-excluded sources.
- Source-family-specific provenance completeness matrix.
- Deterministic canonical ID, alias, collision, and migration policy.
- Required fields and examples for each terminal-state class.
- Representative fixture data that exercises the contract without importing the
  full corpus.
- Validation and test coverage for the manifest contract.

### Excludes (deferred to later phases)

- Full GII TOC discovery.
- Full DSGVO article or recital import.
- State-law source adapters.
- Runtime API additions for coverage or relationship lookup.

## Prerequisites

- [ ] Design spec exists at
      `docs/superpowers/specs/2026-05-15-full-privacy-corpus-design.md`.
- [ ] Current fixture-backed release gate is passing on `main`.
- [ ] Per-phase implementation plan is authored and verified.

## Deliverables

- [ ] Versioned manifest contract and validation rules.
- [ ] Source-family and terminal-state definitions.
- [ ] Canonical ID, alias, collision, and migration policy.
- [ ] Source-family-specific provenance matrix.
- [ ] Failure taxonomy examples for every terminal state.
- [ ] Representative manifest fixtures.
- [ ] Tests proving invalid or incomplete manifest records fail validation.
- [ ] Documentation note describing the manifest as the basis of corpus
      completeness.

## Acceptance Criteria

- [ ] Existing fixture dataset still loads and passes release gates.
- [ ] Manifest validation rejects missing source IDs, missing terminal states,
      duplicate discovered-source records, and unprovenanced exclusions.
- [ ] Manifest validation rejects source records missing required provenance for
      their source family.
- [ ] Canonical ID rules cover generated GII laws, EUR-Lex acts, state-law
      records, third-party relationship records, and new citation units.
- [ ] Every later source family can reference this phase's contract without
      defining its own incompatible manifest shape.

## Dependencies on Other Phases

| Phase | Relationship | Notes |
|-------|-------------|-------|
| Phase 2 | blocks | Generated packages should build on this contract. |
| Phase 3 | blocks | GII discovery needs terminal manifest states. |
| Phase 5 | blocks | DSGVO import should reuse the same provenance model. |

## Notes

This is the recommended starting phase because it prevents GII, EUR-Lex,
state-law, and relationship graph work from diverging on source discovery,
failure reporting, and package metadata.
