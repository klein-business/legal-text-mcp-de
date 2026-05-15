---
type: planning
entity: plan
plan: "full-privacy-corpus"
status: completed
created: "2026-05-15"
updated: "2026-05-15"
---

# Plan: full-privacy-corpus

## Objective

Expand `legal-text-mcp-de` from a fixture-backed legal-audit dataset into a
generated full legal corpus that covers:

- every discoverable official `gesetze-im-internet.de` TOC entry;
- the full DSGVO/GDPR text, including articles 1-99 and recitals;
- the complete `dsgvo-gesetz.de`-style privacy-law scope graph, represented
  through official legal text records and provenance-backed relationship
  metadata;
- German federal privacy neighbor laws, German state privacy laws, and linked EU
  privacy/digital acts such as AI Act and Data Act where official sources are
  available.

The full generated corpus must stay outside Git. The repository should contain
source adapters, manifests, schema/validation code, representative fixtures,
runtime support, tests, and documentation.

## Motivation

The current runtime proves the source-backed MCP/HTTP model on a small fixture
set, but it does not meet the target product scope. Users need reliable access
to the complete official German federal legal catalog and the wider privacy-law
corpus around DSGVO. A generated corpus with explicit source provenance and
failure manifests is required to scale without silently dropping sources or
committing large generated data into the repository.

## Requirements

### Functional

- [x] Discover every `<item>` from
      `https://www.gesetze-im-internet.de/gii-toc.xml`.
- [x] Create exactly one manifest entry for every discovered GII TOC item.
- [x] Import every parseable official GII `xml.zip` into normalized law and norm
      records.
- [x] Assign every discovered GII item exactly one terminal manifest state:
      `imported`, `unsupported_format`, `source_unavailable`, `parse_failed`, or
      `excluded_by_policy`.
- [x] Import DSGVO articles 1-99 from official EUR-Lex/Cellar sources.
- [x] Import DSGVO recitals as first-class citation units.
- [x] Include BDSG, TDDDG, and other German federal privacy neighbor laws through
      GII when available.
- [x] Treat BDSG and TDDDG as critical named GII laws that must import and
      resolve from GII provenance unless an upstream source outage makes that
      impossible and is recorded as a release-blocking source limitation.
- [x] Model German state privacy laws as a separate source family with one
      official source adapter or recorded source limitation per state.
- [x] Import linked EU neighbor acts, including AI Act and Data Act, from
      official EUR-Lex/Cellar sources where available.
- [x] Discover the `dsgvo-gesetz.de`-style scope graph and store only
      provenance-backed relationship metadata, not unlicensed editorial text.
- [x] Store relationship metadata in a validated package section with stable
      relationship IDs, relationship types, provenance, and targets that resolve
      to official records or source limitations.
- [x] Preserve existing MCP and HTTP tools for current `par` and `art` citation
      behavior.
- [x] Add support for new citation units such as `recital`, `chapter`, `section`,
      `annex`, and structural containers.
- [x] Define deterministic canonical ID, alias, collision, and migration rules
      for generated GII, EUR-Lex, state-law, relationship, and new citation-unit
      records before bulk import phases start.
- [x] Expose corpus coverage, source limitations, and relationship metadata
      through stable runtime surfaces.

### Non-Functional

- [x] Full generated datasets are excluded from Git.
- [x] Fast CI remains fixture-backed and does not download the full internet
      corpus on every PR.
- [x] Network-heavy corpus checks run only as explicit or scheduled jobs.
- [x] Every text-bearing record includes source provenance, source URL,
      retrieval timestamp, stand date status where available, and content hash.
- [x] Source failures are explicit, queryable, and reproducible from manifests.
- [x] Live corpus validation gates are required explicit or scheduled checks with
      persisted manifest artifacts; they are not optional evidence for full-scope
      claims.
- [x] Runtime startup and search remain practical for the generated production
      package.
- [x] Public API changes are backwards compatible unless explicitly versioned.
- [x] Tools continue to return source text, citations, metadata, and
      relationships, not legal advice or legal conclusions.

## Scope

### In Scope

- Source manifest schema and terminal-state model.
- Source-family-specific provenance matrix and failure taxonomy.
- Deterministic canonical ID, registry alias, and collision policy.
- Generated corpus package format and validation.
- GII TOC discovery and full GII XML ZIP import coverage.
- EUR-Lex/Cellar source support for full DSGVO and linked EU acts.
- DSGVO recitals as first-class citation units.
- Source-family model for official German state law portals.
- `dsgvo-gesetz.de` scope graph discovery for relationship metadata, subject to
  terms, robots policy, and provenance constraints.
- Relationship records and related-norm lookup surfaces.
- Runtime support for larger generated packages.
- Fast fixture gates and separate network-heavy corpus gates.
- Documentation updates for full generated corpus operation.

### Out of Scope

- Copying third-party editorial text from `dsgvo-gesetz.de` without a
  license-compatible basis.
- Providing legal advice, legal classification, or compliance decisions.
- Committing full generated production datasets to Git.
- SaaS user accounts, billing, authorization, tenant isolation, or hosted
  production operations.
- Treating non-official HTML website chrome as part of complete GII legal text
  coverage.

## Definition of Done

- [x] A full corpus import can discover all currently reachable GII TOC entries
      and assign every entry a terminal manifest state.
- [x] All `imported` GII laws and norms are exposed through MCP and HTTP.
- [x] DSGVO articles 1-99 resolve through MCP and HTTP.
- [x] DSGVO recitals resolve through MCP and HTTP as citation units.
- [x] BDSG and TDDDG remain available through GII provenance.
- [x] BDSG and TDDDG have persisted generated-corpus evidence showing successful
      import and MCP/HTTP resolution from GII provenance, or an explicit
      release-blocking upstream source limitation.
- [x] AI Act, Data Act, and other discovered EU neighbor acts resolve through
      official EUR-Lex/Cellar provenance where available.
- [x] Every German state privacy law has either an official source adapter or a
      recorded source limitation.
- [x] The `dsgvo-gesetz.de` scope graph is represented as relationship metadata
      with clear provenance and no copied unlicensed editorial text.
- [x] The generated production corpus is excluded from Git.
- [x] Fast CI passes using representative fixtures.
- [x] Network-heavy corpus gates can validate live discovery/import behavior.
- [x] Live corpus gate artifacts prove terminal-state coverage for every
      discovered GII TOC entry.
- [x] Documentation explains official text provenance, relationship metadata,
      dataset generation, fixture-vs-production differences, and operations.

## Corpus Contracts

### Canonical IDs and Citation Units

Generated IDs must be deterministic and source-family aware:

| Source Family | Law ID Rule | Citation Units | Collision Rule |
| ------------- | ----------- | -------------- | -------------- |
| GII | normalized GII source path, preserving current hand-authored aliases where present | `par`, `art`, `chapter`, `section`, `annex`, structural `container` | collision fails validation unless an explicit alias/migration entry resolves it |
| EUR-Lex/Cellar | stable slug plus CELEX, for example `dsgvo_eu_2016_679` or `ai_act_eu_2024_1689` | `art`, `recital`, `chapter`, `section`, `annex`, structural `container` | CELEX mismatch or duplicate canonical ID fails validation |
| State law | `state:<state-code>/<stable-law-slug>` | source-dependent `par`, `art`, `chapter`, `section`, `annex`, structural `container` | jurisdiction must be encoded; cross-state aliases cannot collapse into one ID |
| Third-party scope graph | no legal-text law ID; relationship-source records only | relationship IDs, not legal text citations | cannot override official text IDs |

Existing `par` and `art` citation behavior must remain backwards compatible.
New units are additive and must have positive and negative resolver/API tests.

### Source-Family Provenance Matrix

| Source Family | Required Provenance |
| ------------- | ------------------- |
| GII | TOC URL, XML ZIP URL, source path, retrieval timestamp, stand date status, content hash, parser version, terminal state |
| EUR-Lex/Cellar | CELEX, Cellar work/expression/document, language, selected version or consolidation policy, source URL, retrieval timestamp, content hash, parser version, terminal state |
| State law | jurisdiction, official source URL, source format, retrieval timestamp, content hash when fetchable, parser/adapter version, terminal state |
| Third-party scope graph | relationship source URL, crawl timestamp, robots/terms decision, relationship type, target official record or source limitation |

### Failure Taxonomy

Every discovered source record must end in exactly one terminal state:

| State | Meaning | Required Fields |
| ----- | ------- | --------------- |
| `imported` | Source produced validated normalized records. | source ID, source URL, content hash, parser version, generated record IDs |
| `unsupported_format` | Source is reachable but cannot be parsed by an approved adapter. | source ID, source URL, content type/format, reason |
| `source_unavailable` | Source is missing, unreachable, or returns an unusable HTTP status. | source ID, source URL, HTTP/status detail, timestamp |
| `parse_failed` | Source format is expected but parser failed. | source ID, source URL, parser version, error class, excerpt-safe diagnostic |
| `excluded_by_policy` | Source is intentionally excluded for legal, robots, or scope reasons. | source ID, source URL, policy reason, decision timestamp |

`excluded_by_policy` must not be used for ordinary parser failures.

## Testing Strategy

- [x] Unit tests for manifest schema, terminal-state validation, and source
      family identifiers.
- [x] Parser tests for GII XML ZIP, EUR-Lex/Cellar articles, EUR-Lex/Cellar
      recitals, state-law adapters, and relationship graph records.
- [x] Fixture tests for representative GII, DSGVO, EU-neighbor, state-law, and
      relationship records.
- [x] Resolver tests for `par`, `art`, `recital`, `annex`, and structural
      containers.
- [x] Runtime tests for corpus coverage, source limitation reporting, and
      relationship lookup.
- [x] Local HTTP/MCP E2E tests against a small generated fixture package.
- [x] Required explicit or scheduled network-heavy checks for GII TOC discovery,
      terminal-state coverage for all discovered GII items, sampled parser
      variant regression, full DSGVO article/recital import, scope graph
      discovery, state-law reachability, and full production corpus smoke builds.
- [x] Persisted full-corpus validation bundle covering GII terminal states, DSGVO
      counts/version/hash, EU neighbor imported-or-limited states, all 16
      state-law outcomes, and relationship graph discovered-or-limited records.
- [x] Documentation link and image checks for `README.md`, `docs/`,
      `docs-legacy/`, and plan artifacts.

## Phases

| Phase | Title | Scope | Status |
|-------|-------|-------|--------|
| 1 | Manifest and corpus contract foundation | [Detail](phases/phase-1.md) | completed |
| 2 | Generated package format and runtime compatibility | [Detail](phases/phase-2.md) | completed |
| 3 | Complete GII discovery coverage | [Detail](phases/phase-3.md) | completed |
| 4 | GII bulk normalization and coverage gates | [Detail](phases/phase-4.md) | completed |
| 5 | Full DSGVO articles and recitals | [Detail](phases/phase-5.md) | completed |
| 6 | DSGVO scope policy and seed graph inventory | [Detail](phases/phase-6.md) | completed |
| 7 | EU neighbor acts source family | [Detail](phases/phase-7.md) | completed |
| 8 | German state-law source family inventory | [Detail](phases/phase-8.md) | completed |
| 9 | German state-law machine-readable and HTML adapters | [Detail](phases/phase-9.md) | completed |
| 10 | German state-law PDF adapters and source limitations | [Detail](phases/phase-10.md) | completed |
| 11 | Runtime coverage and relationship APIs | [Detail](phases/phase-11.md) | completed |
| 12 | Scaling, search, and operational corpus gates | [Detail](phases/phase-12.md) | completed |
| 13 | Documentation, diagrams, and release readiness | [Detail](phases/phase-13.md) | completed |

## Risks & Open Questions

| Risk/Question | Impact | Mitigation/Answer |
|---------------|--------|-------------------|
| GII catalog entries may fail to fetch or parse. | Full corpus completeness could be misrepresented. | Require one terminal manifest state per discovered item and expose failures as coverage data. |
| Full generated corpus may be large. | Runtime startup, memory, and CI runtime could degrade. | Keep data outside Git, benchmark package formats, and use JSONL/sharding or SQLite if needed. |
| `dsgvo-gesetz.de` may not permit reuse of editorial content. | Relationship graph implementation could violate licensing or terms. | Use it as a scope reference only unless license-compatible reuse is confirmed; store provenance and avoid copying editorial text. |
| State law sources are heterogeneous. | One generic parser may not cover all states. | Treat state law as explicit per-jurisdiction adapters with source limitations where needed. |
| EU acts may have multiple versions/languages. | Wrong text version could be served. | Require CELEX, Cellar expression/document metadata, language, retrieval timestamp, and content hash. |
| New citation units may break existing clients if modeled carelessly. | API compatibility risk. | Add units compatibly and preserve existing `par` and `art` behavior. |
| Network-heavy validation is slow or flaky. | PR checks could become unreliable. | Keep PR CI fixture-backed and run network corpus gates separately or on schedule. |
| Full-corpus gates may fail due to upstream source changes. | Releases could block on external instability. | Persist manifests and classify failures by terminal state so source failures are visible without pretending the corpus is complete. |

## Changelog

### 2026-05-15

- Plan created from `docs/superpowers/specs/2026-05-15-full-privacy-corpus-design.md`.
- Review findings addressed: added explicit ID, provenance, failure taxonomy,
  required live corpus gates, bounded EU seed policy, and split state-law
  implementation phases.
- Second review findings addressed: added relationship package contract,
  EUR-Lex/Cellar version policy requirements, and full-corpus validation bundle
  evidence.
- Third review finding addressed: added named critical-GII-law gates for BDSG
  and TDDDG.
- Authored Phase 1-13 implementation plans and reviewed each implementation
  plan to zero Critical, Major, Minor, and Note findings.
- Phase 1 completed: manifest contract, fixtures, release-gate coverage, and
  source-provenance docs landed and passed implementation review with zero
  findings. Phase 2 started.
- Phase 5 completed after rework: official DSGVO Cellar/Formex recitals now
  parse from `<CONSID>` records, full article/recital boundary checks passed
  against DOC_2, and implementation review passed with zero findings. Phase 6
  started.
- Phase 2 completed: generated-package validation, fixtures, release-gate
  coverage, and package/provenance docs landed and passed implementation review
  with zero Critical, Major, Minor, and Note findings. Phase 3 started.
- Phase 3 completed: GII TOC discovery records, count artifact schema, opt-in
  live discovery gate, fixture tests, and coverage docs landed and passed
  implementation review with zero Critical, Major, Minor, and Note findings.
  Phase 4 started.
- Phase 4 completed: fixture-backed GII bulk normalization, terminal-state gate,
  parser variant matrix, critical BDSG/TDDDG gate, and generated package
  evidence landed and passed implementation review with zero Critical, Major,
  Minor, and Note findings. Phase 5 started.
- Phase 6 completed: metadata-only DSGVO scope policy, fallback seed graph,
  AI Act/Data Act CELEX limitations, relationship transformation helpers, and
  generated-package validation landed and passed implementation review with zero
  Critical, Major, Minor, and Note findings. Phase 7 started.
- Phase 7 completed: seed-bound AI Act/Data Act source records now use official
  Publications/Cellar DOC_1 FMX4 ZIP provenance, fixture and opt-in live gates
  import official German text, and implementation review passed with zero
  Critical, Major, Minor, and Note findings. Phase 8 started.
- Phase 8 completed after reachability rework: all 16 German states have
  explicit inventory outcomes, NI/HB/SL are limitation-only, remaining sources
  are classified as stable HTML from current reachability evidence, and
  implementation review passed with zero Critical, Major, Minor, and Note
  findings. Phase 9 started.
- Phase 9 completed after HTML adapter rework: BB and NRW stable HTML sources
  import with clean official text, remaining eligible states produce explicit
  limitations, state-law IDs remain jurisdiction-prefixed, adapter gate
  validation rejects known portal chrome, and implementation review passed with
  zero Critical, Major, Minor, and Note findings. Phase 10 started.
- Phase 10 completed after coverage validation hardening: all 16 states are
  imported or explicitly limited, current inventory records zero PDF adapter
  sources, no PDF extraction or manual state-law text is claimed, and
  implementation review passed with zero Critical, Major, Minor, and Note
  findings. Phase 11 started.
- Phase 11 completed after generated-package E2E and resolver-contract
  hardening: coverage, source limitation, and relationship APIs are exposed
  additively over MCP/HTTP, generated-package and legacy transport E2E pass,
  citation-unit validation is aligned with resolver canonicalization, and
  implementation review passed with zero Critical, Major, Minor, and Note
  findings. Phase 12 started.
- Phase 12 completed after operational gate hardening: fixture-backed release
  verification stays network-free by default, full-corpus bundle evidence
  validates GII terminal coverage, DSGVO source/count/hash evidence, EU/state
  outcomes, relationship validation, critical-law MCP/HTTP resolution, and
  benchmark migration decisions. Implementation review passed with zero
  Critical, Major, Minor, and Note findings. Phase 13 started.
- Phase 13 completed after docs/release-readiness hardening: root README,
  overview, module docs, feature docs, Mermaid diagrams, link/image checks,
  stale workflow checks, and release verification all passed independent
  implementation review with zero Critical, Major, Minor, and Note findings.
- Plan completed: all 13 phases have accepted implementation reviews with zero
  remaining findings, and the final release gate passed.
