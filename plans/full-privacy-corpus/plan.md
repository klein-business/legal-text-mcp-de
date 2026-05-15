---
type: planning
entity: plan
plan: "full-privacy-corpus"
status: draft
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

- [ ] Discover every `<item>` from
      `https://www.gesetze-im-internet.de/gii-toc.xml`.
- [ ] Create exactly one manifest entry for every discovered GII TOC item.
- [ ] Import every parseable official GII `xml.zip` into normalized law and norm
      records.
- [ ] Assign every discovered GII item exactly one terminal manifest state:
      `imported`, `unsupported_format`, `source_unavailable`, `parse_failed`, or
      `excluded_by_policy`.
- [ ] Import DSGVO articles 1-99 from official EUR-Lex/Cellar sources.
- [ ] Import DSGVO recitals as first-class citation units.
- [ ] Include BDSG, TDDDG, and other German federal privacy neighbor laws through
      GII when available.
- [ ] Treat BDSG and TDDDG as critical named GII laws that must import and
      resolve from GII provenance unless an upstream source outage makes that
      impossible and is recorded as a release-blocking source limitation.
- [ ] Model German state privacy laws as a separate source family with one
      official source adapter or recorded source limitation per state.
- [ ] Import linked EU neighbor acts, including AI Act and Data Act, from
      official EUR-Lex/Cellar sources where available.
- [ ] Discover the `dsgvo-gesetz.de`-style scope graph and store only
      provenance-backed relationship metadata, not unlicensed editorial text.
- [ ] Store relationship metadata in a validated package section with stable
      relationship IDs, relationship types, provenance, and targets that resolve
      to official records or source limitations.
- [ ] Preserve existing MCP and HTTP tools for current `par` and `art` citation
      behavior.
- [ ] Add support for new citation units such as `recital`, `chapter`, `section`,
      `annex`, and structural containers.
- [ ] Define deterministic canonical ID, alias, collision, and migration rules
      for generated GII, EUR-Lex, state-law, relationship, and new citation-unit
      records before bulk import phases start.
- [ ] Expose corpus coverage, source limitations, and relationship metadata
      through stable runtime surfaces.

### Non-Functional

- [ ] Full generated datasets are excluded from Git.
- [ ] Fast CI remains fixture-backed and does not download the full internet
      corpus on every PR.
- [ ] Network-heavy corpus checks run only as explicit or scheduled jobs.
- [ ] Every text-bearing record includes source provenance, source URL,
      retrieval timestamp, stand date status where available, and content hash.
- [ ] Source failures are explicit, queryable, and reproducible from manifests.
- [ ] Live corpus validation gates are required explicit or scheduled checks with
      persisted manifest artifacts; they are not optional evidence for full-scope
      claims.
- [ ] Runtime startup and search remain practical for the generated production
      package.
- [ ] Public API changes are backwards compatible unless explicitly versioned.
- [ ] Tools continue to return source text, citations, metadata, and
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

- [ ] A full corpus import can discover all currently reachable GII TOC entries
      and assign every entry a terminal manifest state.
- [ ] All `imported` GII laws and norms are exposed through MCP and HTTP.
- [ ] DSGVO articles 1-99 resolve through MCP and HTTP.
- [ ] DSGVO recitals resolve through MCP and HTTP as citation units.
- [ ] BDSG and TDDDG remain available through GII provenance.
- [ ] BDSG and TDDDG have persisted generated-corpus evidence showing successful
      import and MCP/HTTP resolution from GII provenance, or an explicit
      release-blocking upstream source limitation.
- [ ] AI Act, Data Act, and other discovered EU neighbor acts resolve through
      official EUR-Lex/Cellar provenance where available.
- [ ] Every German state privacy law has either an official source adapter or a
      recorded source limitation.
- [ ] The `dsgvo-gesetz.de` scope graph is represented as relationship metadata
      with clear provenance and no copied unlicensed editorial text.
- [ ] The generated production corpus is excluded from Git.
- [ ] Fast CI passes using representative fixtures.
- [ ] Network-heavy corpus gates can validate live discovery/import behavior.
- [ ] Live corpus gate artifacts prove terminal-state coverage for every
      discovered GII TOC entry.
- [ ] Documentation explains official text provenance, relationship metadata,
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

- [ ] Unit tests for manifest schema, terminal-state validation, and source
      family identifiers.
- [ ] Parser tests for GII XML ZIP, EUR-Lex/Cellar articles, EUR-Lex/Cellar
      recitals, state-law adapters, and relationship graph records.
- [ ] Fixture tests for representative GII, DSGVO, EU-neighbor, state-law, and
      relationship records.
- [ ] Resolver tests for `par`, `art`, `recital`, `annex`, and structural
      containers.
- [ ] Runtime tests for corpus coverage, source limitation reporting, and
      relationship lookup.
- [ ] Local HTTP/MCP E2E tests against a small generated fixture package.
- [ ] Required explicit or scheduled network-heavy checks for GII TOC discovery,
      terminal-state coverage for all discovered GII items, sampled parser
      variant regression, full DSGVO article/recital import, scope graph
      discovery, state-law reachability, and full production corpus smoke builds.
- [ ] Persisted full-corpus validation bundle covering GII terminal states, DSGVO
      counts/version/hash, EU neighbor imported-or-limited states, all 16
      state-law outcomes, and relationship graph discovered-or-limited records.
- [ ] Documentation link and image checks for `README.md`, `docs/`,
      `docs-legacy/`, and plan artifacts.

## Phases

| Phase | Title | Scope | Status |
|-------|-------|-------|--------|
| 1 | Manifest and corpus contract foundation | [Detail](phases/phase-1.md) | pending |
| 2 | Generated package format and runtime compatibility | [Detail](phases/phase-2.md) | pending |
| 3 | Complete GII discovery coverage | [Detail](phases/phase-3.md) | pending |
| 4 | GII bulk normalization and coverage gates | [Detail](phases/phase-4.md) | pending |
| 5 | Full DSGVO articles and recitals | [Detail](phases/phase-5.md) | pending |
| 6 | DSGVO scope policy and seed graph inventory | [Detail](phases/phase-6.md) | pending |
| 7 | EU neighbor acts source family | [Detail](phases/phase-7.md) | pending |
| 8 | German state-law source family inventory | [Detail](phases/phase-8.md) | pending |
| 9 | German state-law machine-readable and HTML adapters | [Detail](phases/phase-9.md) | pending |
| 10 | German state-law PDF adapters and source limitations | [Detail](phases/phase-10.md) | pending |
| 11 | Runtime coverage and relationship APIs | [Detail](phases/phase-11.md) | pending |
| 12 | Scaling, search, and operational corpus gates | [Detail](phases/phase-12.md) | pending |
| 13 | Documentation, diagrams, and release readiness | [Detail](phases/phase-13.md) | pending |

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
