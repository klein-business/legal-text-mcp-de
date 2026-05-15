---
type: design
topic: full-privacy-corpus
date: 2026-05-15
status: review
---

# Full Privacy Corpus Design

## Decision

The target scope is complete coverage of the legal corpus represented by
`dsgvo-gesetz.de` plus the complete official `gesetze-im-internet.de` catalog.
This expands the project from a fixture-backed legal audit dataset into a
generated production corpus.

The implementation must use official legal text sources as the authoritative
text source. Third-party sites such as `dsgvo-gesetz.de` may be used as coverage
and relationship references only when their terms, robots policy, and provenance
constraints allow it. Editorial text from third-party sites must not be copied
into the normalized corpus unless there is an explicit license-compatible basis.

## Current Gap

The current repository supports a focused fixture set:

- 10 law records in `mcp/tests/fixtures/normalized/laws.json`.
- 34 norm records in `mcp/tests/fixtures/normalized/norms.json`.
- 9 selected German federal sources from `gesetze-im-internet.de`.
- DSGVO from official EUR-Lex/Cellar, but only selected articles:
  `5`, `6`, `12`, `13`, `14`, `15`, `17`, `21`, `25`, `32`, and `82`.

The official `gesetze-im-internet.de/gii-toc.xml` catalog currently exposes
thousands of XML ZIP entries. The full target also includes DSGVO articles,
recitals, topic relationships, German federal privacy laws, German state privacy
laws, and linked EU digital/privacy acts such as the AI Act and Data Act when
they are part of the discovered `dsgvo-gesetz.de` coverage graph.

## Source Families

### German Federal Law

Authoritative source:

- `https://www.gesetze-im-internet.de/gii-toc.xml`
- every listed `xml.zip` source entry

Coverage:

- all GII catalog entries, not only the current hand-picked source matrix
- all parseable norms, structural containers, titles, stand dates, source URLs,
  and content hashes

The importer must preserve source failures in a manifest instead of silently
dropping entries. A generated dataset can be incomplete only when the manifest
records the exact failed source and error class.

### EU Privacy And Digital Law

Authoritative source:

- EUR-Lex / Publications Office / Cellar

Required EU coverage:

- DSGVO / GDPR, Regulation (EU) 2016/679, CELEX `32016R0679`
- all DSGVO articles 1-99
- all DSGVO recitals as first-class citation units
- linked EU privacy and digital acts discovered from the `dsgvo-gesetz.de`
  scope graph, including AI Act and Data Act where official German-language
  EUR-Lex text is available

EU records must retain CELEX, Cellar work/expression/document metadata,
language, retrieval timestamp, and content hash.

### German Privacy Neighbor Laws

Authoritative sources:

- BDSG, TDDDG, and other German federal laws from GII where available
- state privacy laws from official state law portals, modeled as a separate
  source family because they are not part of GII

Required coverage:

- federal German privacy-law references linked from the target graph
- all 16 German state privacy laws where official machine-readable or stable
  HTML/PDF sources can be identified
- relationship metadata between DSGVO articles/recitals and the related German
  implementation or sector laws where the source graph supports it

State-law source adapters must be explicit per jurisdiction. If a state does not
offer a stable machine-readable source, the manifest must record that as a
source limitation rather than inventing text.

### DSGVO-Gesetz Scope Graph

`dsgvo-gesetz.de` is treated as a scope and relationship reference:

- pages for DSGVO articles
- pages for DSGVO recitals
- topic/category pages
- links to BDSG, TDDDG, LDSG, AI Act, Data Act, and other neighboring legal
  resources

The normalized corpus should store relationship metadata such as
`related_to`, `implements`, `explains`, `recital_for`, and `topic_for` only with
clear provenance. The project must distinguish official legal text from curated
relationship metadata.

## Data Model

The current model is too narrow for the full target because `NormUnit` only
supports `par` and `art`. The corpus model needs these additional concepts:

- `source_family`: `gii`, `eur_lex_cellar`, `state_law`, `third_party_scope`
- `jurisdiction`: `DE`, German state code, or `EU`
- `document_kind`: law, regulation, directive, recital set, topic graph, or
  external reference
- citation units: paragraph, article, recital, chapter, section, annex, and
  structural container
- relationship records with source provenance
- generated manifest entries for every discovered source

The public API should remain backwards compatible for existing `par` and `art`
citations. New units should be additive, for example:

- `dsgvo_eu_2016_679/art:15`
- `dsgvo_eu_2016_679/recital:63`
- `ai_act_eu_2024_1689/art:1`
- `bdsg_2018/par:1`
- `state:be/berliner-dsg/par:1`

## Corpus Pipeline

The generated production corpus should be built by a staged pipeline:

1. Discover source entries.
2. Fetch source payloads with caching, hashes, retries, and rate limits.
3. Parse source-specific formats into normalized records.
4. Validate required identifiers, source metadata, text presence, and citation
   stability.
5. Build search indexes and relationship indexes.
6. Write a dataset package with a manifest, readiness file, laws, norms,
   relationship records, and source-failure report.

The pipeline must support incremental updates. A source whose hash has not
changed should not be reparsed unless the parser version changed.

## Runtime Architecture

The MCP and HTTP runtime should continue to serve a mounted normalized dataset.
The full corpus should not be committed to Git.

The runtime should evolve from the current small JSON fixture loader to a loader
that can handle full generated packages. The first production implementation can
still use JSON or JSONL if benchmarks are acceptable; if startup or memory use is
too high, the package format should move to sharded JSONL or SQLite-backed
lookup while preserving the API response contracts.

Required runtime capabilities:

- list and search laws across all source families
- resolve exact citations for paragraphs, articles, recitals, and annexes
- return official source provenance for every text-bearing unit
- return relationship metadata separately from legal text
- report dataset readiness and source limitations

## API And Tool Surface

Existing tools should remain stable:

- `list_laws`
- `get_law`
- `get_norm`
- `resolve_citation`
- `search_laws`
- `get_source_metadata`

Likely additive tools or endpoints:

- `list_corpus_sources`: show source families, jurisdictions, and manifest
  status
- `get_related_norms`: return article/recital/topic/law relationships with
  provenance
- `get_corpus_coverage`: report expected vs imported source counts and failures

The runtime must continue to avoid legal advice, legal classification, and
hallucinated fallback generation.

## Documentation Design

The existing docs should be updated after implementation:

- `docs/features/supported-laws.md`: replace fixture-only wording with generated
  full-corpus coverage and a fixture-subset explanation
- `docs/features/source-provenance.md`: document source families, official text
  provenance, third-party relationship provenance, and source limitations
- `docs/features/law-loading-and-indexing.md`: document generated package
  loading, manifest validation, and relationship indexes
- `docs/features/mcp-law-tools.md`: document new citation units and related-law
  lookup if added
- `docs/overview.md`: add Mermaid architecture and sequence diagrams for
  discovery, normalization, package loading, and citation resolution

## Verification Strategy

Fast CI should not download the full internet corpus on every PR. It should run:

- unit tests for every parser and source adapter
- fixture tests for representative GII, EUR-Lex, state-law, and relationship
  graph records
- manifest validation tests
- citation resolver tests for `par`, `art`, `recital`, and structural containers
- docs link and image checks
- local HTTP/MCP E2E checks against a small generated fixture package

Network-heavy checks should run as explicit or scheduled jobs:

- GII catalog discovery count and schema validation
- sampled GII ZIP fetch and parse
- full DSGVO articles and recitals import
- dsgvo-gesetz.de scope graph discovery, subject to robots and terms checks
- official state-law source reachability checks
- full production corpus build smoke test

## Risks And Controls

- Third-party editorial content: use `dsgvo-gesetz.de` for scope mapping only
  unless license-compatible reuse is confirmed.
- State law heterogeneity: require one adapter per official state source family.
- Dataset size: keep full generated data outside Git and benchmark loader
  behavior before choosing final package format.
- Source instability: manifest every failure with URL, status, timestamp, and
  parser error class.
- Citation ambiguity: keep canonical IDs source-family aware and avoid
  cross-source aliases that hide jurisdiction.
- Legal advice boundary: tools return texts, citations, metadata, and
  relationships, not legal conclusions.

## Acceptance Criteria

The work is complete only when:

- the generated corpus can import all currently discoverable GII TOC entries or
  record explicit source failures
- DSGVO articles 1-99 resolve through the MCP and HTTP APIs
- DSGVO recitals resolve as citation units
- BDSG and TDDDG are included through GII where available
- all discovered `dsgvo-gesetz.de` scope links are represented either as
  official-text records, official-source limitations, or third-party relationship
  metadata with provenance
- state privacy laws have official source adapters or recorded source
  limitations per state
- AI Act, Data Act, and other discovered EU neighbor acts resolve through
  official EUR-Lex/Cellar sources where available
- full generated data is excluded from Git
- CI has fast fixture gates and separate network-heavy corpus gates
- documentation explains official text provenance, relationship metadata, and
  the difference between fixture and production datasets

## User Review Questions

The approved scope is complete coverage of GII and the full
`dsgvo-gesetz.de`-style privacy corpus. The remaining review decision is whether
the first implementation plan should start with:

1. DSGVO articles and recitals first, then expand outward.
2. GII bulk corpus first, then expand DSGVO relationships.
3. Source-manifest infrastructure first, then implement each source family.

The recommended path is option 3 because it prevents every later source adapter
from inventing its own discovery, failure, provenance, and package format.
