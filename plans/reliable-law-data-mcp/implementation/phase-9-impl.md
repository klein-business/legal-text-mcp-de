---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 9
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 9 - Fixture Coverage, Docs, and Release Gate

> Implements [Phase 9](../phases/phase-9.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 9 closes Phase 1 with verification, documentation, and release-gate artifacts. It should not introduce new source pipelines, parsers, transports, or product features. Instead it adds conformance tests and reports that prove the Phase 1 fixture inventory, source matrix, resolver/search/MCP/HTTP contracts, structured errors, runtime packaging, and documentation match the implemented system.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| `mcp/tests/test_fixture_coverage.py` | create | Assert required fixture inventory coverage across normalized records, citation goldens, search fixtures, MCP, and HTTP where applicable. |
| `mcp/tests/fixtures/fixture_inventory_expected.json` | create | Machine-readable oracle for the Phase 1 fixture inventory, cross-checked against `fixture-inventory.md`. |
| `mcp/tests/test_error_contracts.py` | create/modify | Cross-service structured error conformance for resolver, search, MCP, and HTTP. |
| `mcp/tests/test_release_gate.py` | create | Release checks for no production `bundestag/gesetze` dependency, no SaaS/billing/tenant scope, and runtime packaging defaults. |
| `mcp/tests/test_source_matrix_live.py` | create/modify | Live source-matrix probe re-verification for valid and known-invalid paths. |
| `scripts/verify_phase1_release.py` | create | Single release-gate verification command that runs live source probes, report checks, docs checks, and the full pytest suite. |
| `plans/reliable-law-data-mcp/release-gate.md` | create | Human-readable Phase 1 pass/fail checklist and verification evidence. |
| `plans/reliable-law-data-mcp/source-verification.md` | create | Source matrix probe report with timestamps, statuses, and known issues. |
| `docs/features/supported-laws.md` | create/modify | Document Phase 1 supported laws, aliases, source kinds, and coverage limits. |
| `docs/features/source-provenance.md` | create/modify | Document raw/normalized data provenance, manifests, hashes, stand date status, and known source issues. |
| `docs/features/api-contracts.md` | create/modify | Document MCP and HTTP response contracts and error shapes. |
| `docs/features/known-issues.md` | create/modify | Document known source and parsing limitations such as EGBGB container URL status. |
| `docs/overview.md` and `docs/modules/*.md` | modify | Reconcile module/feature inventories after Phases 1-8. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global DoD, testing strategy, no-SaaS scope, and release requirements. |
| `plans/reliable-law-data-mcp/phases/phase-9.md` | Gated Phase 9 scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | Shared response schemas, error codes, readiness, MCP, HTTP, and search contracts. |
| `plans/reliable-law-data-mcp/source-matrix.md` | Source-probe truth table and known invalid paths. |
| `plans/reliable-law-data-mcp/fixture-inventory.md` | Required citation and coverage inventory. |
| `plans/reliable-law-data-mcp/implementation/phase-1-impl.md` through `phase-8-impl.md` | Phase-specific verification expectations and boundaries. |
| `mcp/tests/golden/` | Golden JSON coverage for resolver/search/MCP/HTTP outputs. |
| `mcp/tests/fixtures/normalized/` | Normalized fixture package used for conformance tests. |
| `Dockerfile` | Runtime packaging verification target. |
| `mcp/config.py`, `mcp/server.py`, `mcp/http_api.py` | Production runtime dependency and readiness verification targets. |
| `docs/` and `README.md` | Documentation update targets; final root README reconciliation is also covered by the later `update-docs` request. |

## Release Gate Contract

Phase 9 must produce:

- a machine-enforced fixture coverage test that fails if any citation from the machine-readable fixture oracle or `fixture-inventory.md` lacks normalized data, service-level golden JSON, and transport coverage where the transport exists;
- a source verification report for every `source-matrix.md` row, including valid official URLs and known invalid paths such as `tddsg` and `pangv`;
- a structured error contract test covering `LAW_NOT_FOUND`, `NORM_NOT_FOUND`, `AMBIGUOUS_LAW_ALIAS`, `SOURCE_UNAVAILABLE`, `DATASET_NOT_READY`, `INVALID_CITATION`, and `INVALID_QUERY`;
- a runtime dependency scan proving production startup, Docker packaging, and current docs do not rely on `bundestag/gesetze`;
- documentation that states supported Phase 1 laws, source provenance, known limitations, and explicit non-goals;
- a `release-gate.md` checklist with command outputs, pass/fail status, residual risks, and confirmation that no SaaS, billing, auth, or tenancy scope was introduced.

Legacy/archive references are allowed only when clearly non-production: `docs-legacy/**`, plan history/reviews, and `prepare_data` references to external preparation tooling. Production entrypoints (`Dockerfile`, `mcp/server.py`, `mcp/config.py`, `mcp/http_api.py`, and `mcp/legal_texts/**`) must not use `bundestag/gesetze`.

## Implementation Steps

### Step 1: Add Fixture Coverage Conformance Tests

- **What**: Add `fixture_inventory_expected.json`, verify it matches `fixture-inventory.md`, and assert required normalized records, citation goldens, search fixtures, MCP responses, and HTTP responses exist.
- **Where**: `mcp/tests/fixtures/fixture_inventory_expected.json` and `mcp/tests/test_fixture_coverage.py`.
- **Why**: Phase 9 should re-verify, not discover, fixture gaps.
- **Considerations**: Include BDSG and DSGVO full fixture sets, EGBGB container/child, suffix norms, and PAngV/TDDDG alias cases. Tests should fail with the missing canonical ID and coverage type.

### Step 2: Add Cross-Transport Error Contract Tests

- **What**: Verify every structured error code through the service layer and through MCP/HTTP where reachable.
- **Where**: `mcp/tests/test_error_contracts.py`.
- **Why**: Error shape consistency is part of the Phase 1 legal reliability contract.
- **Considerations**: Do not assert only status codes; assert `error.code`, `error.message`, `error.details`, bounded `suggestions`, and source metadata where applicable.

### Step 3: Re-Verify Source Matrix

- **What**: Add or finalize live source-probe tests and write a source verification report.
- **Where**: `mcp/tests/test_source_matrix_live.py`, `scripts/verify_phase1_release.py`, and `plans/reliable-law-data-mcp/source-verification.md`.
- **Why**: The plan requires source paths to be verified and known invalid upstream paths to remain regression checks.
- **Considerations**: Tests should assert behavior without silently rewriting tracked reports. The release verification script may update or check `source-verification.md` deliberately. Record retrieval timestamp, URL, expected/actual status, content-type/hash where available, and known issue reason. DSGVO must verify German Cellar expression `0004.02` `DOC_2` with German article XML anchors. This release-gate command is allowed to require network access.

### Step 4: Add Release Dependency and Scope Scans

- **What**: Verify no production dependency on `bundestag/gesetze`, no production default `/app/gesetze/`, no double-serialized MCP returns, and no SaaS/billing/tenant additions.
- **Where**: `mcp/tests/test_release_gate.py`.
- **Why**: Phase 1 is reliability-focused and must not leave demo production paths or product-scope creep.
- **Considerations**: Use an explicit allowlist for `docs-legacy/**`, plan history, and `prepare_data` external-tool references. Production scans cover `Dockerfile`, `mcp/config.py`, `mcp/server.py`, `mcp/http_api.py`, and `mcp/legal_texts/**`.

### Step 5: Review Golden JSON Outputs

- **What**: Add tests or fixtures that compare representative citation, search, MCP, and HTTP responses against golden JSON.
- **Where**: `mcp/tests/golden/` and conformance tests.
- **Why**: Golden coverage prevents accidental contract drift after implementation.
- **Considerations**: Ignore only explicitly volatile fields such as retrieval timestamps when tests define stable comparison rules. Do not ignore canonical IDs, URLs, source kind, source identifiers, titles, text/status, errors, or scores.

### Step 6: Update Support and Provenance Documentation

- **What**: Document supported laws, aliases, source paths, DSGVO/EUR-Lex separation, manifests, hashes, readiness, and known issues.
- **Where**: `docs/features/supported-laws.md`, `docs/features/source-provenance.md`, and `docs/features/known-issues.md`.
- **Why**: Users need to know what Phase 1 safely supports and what remains out of scope.
- **Considerations**: Do not claim all German laws are supported. State that no legal advice, SaaS, billing, auth, or tenancy features are included.

### Step 7: Update API Contract Documentation

- **What**: Document MCP tools, HTTP endpoints, OpenAPI location, response wrappers, structured errors, and examples including EGBGB child norm path.
- **Where**: `docs/features/api-contracts.md`, `docs/features/mcp-law-tools.md`, `docs/features/http-api.md`, and `docs/modules/mcp-server.md`.
- **Why**: Phase 1 contracts must be usable by agents and humans.
- **Considerations**: Keep examples generated from implemented fixtures where possible. Root README is reconciled in the later explicit `update-docs` step requested by the user.

### Step 8: Write Release Gate Artifact

- **What**: Create `plans/reliable-law-data-mcp/release-gate.md` with status, commands run, pass/fail outcomes, supported law list, known issues, residual risks, and non-goal confirmation.
- **Where**: `plans/reliable-law-data-mcp/release-gate.md`.
- **Why**: The release gate should be auditable after implementation and review.
- **Considerations**: Include the exact date, dataset ID or fixture package ID, source verification timestamp, and final test command output summary.

### Step 9: Add Single Release Verification Entrypoint

- **What**: Add one script that runs live source verification, release scans, docs/link checks, and the complete pytest suite in the required order.
- **Where**: `scripts/verify_phase1_release.py`.
- **Why**: The final gate should be reproducible as one command instead of a handwritten sequence.
- **Considerations**: The script should fail non-zero on any test or verification failure and print a concise summary suitable for `release-gate.md`.

## Testing Plan

Primary verify command:

```bash
PYTHONPATH=mcp python3 scripts/verify_phase1_release.py
```

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Fixture coverage | Every citation in `fixture-inventory.md` across normalized records, goldens, resolver, MCP, and HTTP. | Missing coverage fails with canonical ID and missing layer. |
| Source matrix live probes | Valid official URLs and known invalid paths. | Status/content expectations match; report artifact is updated. |
| Golden JSON conformance | Representative citations/search/MCP/HTTP outputs. | Stable fields match exactly; volatile fields ignored only by explicit rule. |
| Error contracts | All structured errors across reachable layers. | Error code, details, suggestions, source metadata, and HTTP/MCP shapes are consistent. |
| Runtime dependency scan | Production entrypoints and packaging. | No production `bundestag/gesetze` dependency and no `/app/gesetze/` default serving path. |
| No product-scope creep | Source scan and release checklist. | No SaaS, billing, auth, tenancy, or user-account behavior introduced. |
| Documentation checks | Supported laws, provenance, API contracts, known issues, and docs links. | Docs reflect implemented behavior and links resolve. |
| Full regression | All Phase 1 tests. | Complete suite passes. |
| Release script | `scripts/verify_phase1_release.py`. | Runs source probes, release scans, docs checks, and pytest suite; exits non-zero on failure. |

### Test Integrity Constraints

- Do not waive fixture, source, error, MCP, or HTTP failures by weakening assertions.
- Live source matrix failures must be recorded as release blockers unless the source matrix is updated with a reviewed known issue.
- Documentation must not overclaim supported laws or legal interpretation capability.

## Rollback Strategy

Remove Phase 9 conformance tests, release reports, and Phase 9 documentation additions. Do not remove or roll back Phase 1-8 implementation code unless a release gate failure identifies a concrete implementation defect that must be fixed in its owning phase.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Live source probes in release gate | mandatory / optional marker / mocked only | mandatory release-gate script | Source reliability is a core Phase 1 requirement. |
| Production dependency scan | scan all repo text / scan production entrypoints with allowlist / manual only | production entrypoints with explicit allowlist | Avoids false positives from archived docs and plan history while checking real runtime paths. |
| Release artifact location | docs only / plans only / both | plans release-gate artifact plus docs summaries | Keeps auditable gate evidence with the plan and user-facing summaries in docs. |
| Root README update | Phase 9 / final `update-docs` step / skip | final `update-docs` step | User explicitly requested a later docs update including root README and repo rename. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `plans/reliable-law-data-mcp/fixture-inventory.md` | required citation rows | Defines the final coverage oracle. |
| `plans/reliable-law-data-mcp/source-matrix.md` | official and known-invalid URLs | Defines source verification scope. |
| `Dockerfile` | production packaging | Must no longer clone demo data after Phase 7. |
| `README.md` and `docs/**` | current docs | Still describe legacy behavior before implementation/docs updates. |
| `mcp/tests/` | existing and planned tests | Release gate consolidates all test layers. |

### Mismatches / Notes

- Current docs and README still describe the legacy Markdown server; Phase 9 documents implemented Phase 1 behavior, and the later `update-docs` pass reconciles root README and repository rename.
- Live source checks can fail due to upstream availability; those failures should block release unless converted into a reviewed known issue with source evidence.
- This phase should not add new laws or new API behavior; gaps should be fixed in the earlier owning implementation area.
