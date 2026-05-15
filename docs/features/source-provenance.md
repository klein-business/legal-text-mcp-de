---
type: documentation
entity: feature
feature: "source-provenance"
version: 1.9
---

# Feature: source-provenance

> Part of [legal-text-mcp-de](../overview.md)

## Summary

Every law and norm response carries provenance. Clients can distinguish German GII sources from the DSGVO Cellar source, inspect URLs and hashes, and avoid treating fixture text as untraceable model output.

## Metadata Fields

| Field | Purpose |
| ----- | ------- |
| `source_kind` | `gesetze-im-internet`, `eur-lex-cellar`, or `state-law`. |
| `source_identifier` | GII source path, CELEX identifier, or state-law source identifier. |
| `source_url` | Canonical import/source URL. |
| `retrieved_at` | Snapshot retrieval timestamp. |
| `stand_date` | Source stand date when available. |
| `stand_date_status` | Whether stand date is available, missing, or not exposed by the source. |
| `content_hash` | SHA-256 over the source or normalized content. |
| `source_metadata` | Source-kind-specific fields such as Cellar work/expression/document. |
| `known_issues` | Backwards-compatible field for structured source anomalies and non-fatal provenance caveats. |

## Data Separation

Raw snapshots and normalized data are separate:

- raw snapshots: `data/sources/raw/{snapshot_id}/` (ignored local data);
- normalized serving packages: `data/normalized/{dataset_id}/` (ignored local data);
- committed test fixtures: `mcp/tests/fixtures/normalized/`.

## Corpus Manifest Contract

The generated full corpus uses a versioned `corpus-manifest.v1` contract as the
source-completeness record. The manifest is separate from the current serving
dataset loader: fixture packages can still load without a corpus manifest, while
generation and coverage gates can validate discovered sources, imported records,
source limitations, and policy exclusions explicitly.

Manifest source families are:

| Source Family | Meaning |
| ------------- | ------- |
| `gii` | Official `gesetze-im-internet.de` TOC and XML ZIP sources. |
| `eur-lex-cellar` | Official EUR-Lex / Cellar records such as DSGVO. |
| `state-law` | German state privacy-law source inventories and adapters. |
| `third-party-scope` | Relationship-source metadata only; never legal-text law IDs. |

Every terminal coverage source has exactly one terminal state:

| Terminal State | Meaning |
| -------------- | ------- |
| `imported` | Source produced validated normalized law or norm records. |
| `unsupported_format` | Source is reachable but no approved adapter supports the format. |
| `source_unavailable` | Source is missing, unreachable, or returns an unusable status. |
| `parse_failed` | Source format is expected, but parsing failed with diagnostics. |
| `excluded_by_policy` | Source is intentionally excluded for legal, robots, or scope reasons. |

Relationship-source metadata must point at official records or source
limitations. Third-party scope sources must not create legal-text canonical IDs
and must not copy editorial text into the generated package.

## GII Discovery Artifacts

Complete GII coverage starts from the official TOC at
`https://www.gesetze-im-internet.de/gii-toc.xml`. Discovery parses every TOC
`<item>` with an `xml.zip` link into one `gii` manifest source record using
`source_id="gii:<source_path>"`, normalized HTTPS `xml_zip_url`, derived
`index_url`, `toc_url`, TOC content hash, and parser version. Curated aliases
from the existing source matrix are recorded as alias candidates and do not
replace the TOC-derived source ID.

The opt-in live gate writes `gii-discovery-artifact.v1` JSON with the TOC URL,
retrieval timestamp, TOC SHA-256, parser version, numeric
`discovered_gii_items`, `source_path_count`, `duplicate_count`,
`discovered_gii_records`, `source_paths`, malformed-item diagnostics,
`toc_limitation` when the TOC cannot be fetched or parsed, validation errors,
and an embedded discovery-mode corpus manifest. Non-empty malformed-item
diagnostics are validation failures. This artifact proves discovery coverage
and current TOC count; it does not claim that every discovered `xml.zip` was
imported.

## GII Terminal-State Gates

Bulk GII fixture gates consume discovery records and assign exactly one terminal
state per discovered source. Imported sources reference generated law and norm
IDs; unavailable, unsupported, and parse-failed sources become source limitation
records rather than fake law or norm records. The gate writes
`gii-corpus-gate.v1` evidence with terminal-state counts, validation errors,
generated-package hash, parser variant matrix path/version/hash, and
critical-law outcomes. Missing local payloads are local gate failures by
default; they are not treated as official upstream outages.

GII source paths remain provenance identifiers. Generated legal-text IDs use the
stable canonical ID where one already exists. For example, upstream source path
`ttdsg` remains `source_id="gii:ttdsg"` and `source_metadata.source_path`, while
the generated TDDDG law ID remains `tdddg`.

BDSG (`bdsg_2018`) and TDDDG (`ttdsg` source path, `tdddg` canonical ID) are
critical GII privacy laws. The gate accepts them only when they are imported and
resolvable from GII provenance through runtime, MCP, and HTTP evidence from the
generated GII package, or when an explicit release-blocking upstream
`source_unavailable` limitation proves official source unavailability. Reachable
`parse_failed` or `unsupported_format` outcomes fail the critical-law gate.

## DSGVO Cellar Policy

DSGVO text uses official EUR-Lex/Cellar provenance, not third-party editorial
sources. Generated DSGVO records carry CELEX `32016R0679`, selected Cellar
work/expression/document metadata, German language, retrieval timestamp,
version/consolidation policy, and content hash. Articles use `art:<n>` citation
units; recitals use `recital:<n>` citation units. The opt-in full-count gate
verifies generated package counts and boundary samples for articles 1 and 99
and recitals 1 and 173 against the pinned source policy.

## EU Neighbor Source Policy

EU neighbor acts are bounded by the approved privacy scope seed graph rather
than discovered by an unbounded EUR-Lex crawler. Phase 7 starts with AI Act
CELEX `32024R1689` and Data Act CELEX `32023R2854`; additional EU acts require
an explicit seed entry before import. Generated neighbor records use official
German EUR-Lex/Cellar provenance with CELEX, language, selected version or
document policy, source URL, retrieval timestamp, and content hash. AI Act and
Data Act source records point at Publications Office / Cellar `DOC_1` FMX4 ZIP
items and retain the human EUR-Lex URL separately as policy metadata.

Seeded EU neighbor acts must end as either imported official records or
source-limitation records. Missing, unreachable, unsupported, or parse-failed
official German text is represented as source limitations so relationship
targets resolve to package records instead of external strings. The opt-in
`verify_eu_neighbor_sources.py` evidence script writes `eu-neighbor-sources.v1`
artifacts for fixture or local source checks; it is not part of the default
release gate.

The final full-corpus bundle requires seeded CELEX coverage for at least AI Act
`32024R1689` and Data Act `32023R2854`. Imported neighbor results retain
canonical ID, source URL, version policy, and generated norm IDs. Limited
neighbor results retain source-limitation evidence.

## State-Law Inventory Policy

State privacy-law coverage starts with an inventory, not parser or runtime
serving claims. Each German state has one `state-law` inventory record with a
canonical ID of the form `state:<state-code>/<stable-law-slug>`, official source
candidates, source format, adapter class, reachability evidence, and a
stability note. Adapter classes route later work to machine-readable or stable
HTML adapters in Phase 9, PDF handling in Phase 10, or a limitation-only
outcome when no stable usable official source is approved.

Limitation-only state records reference committed `state-law` source limitation
records instead of dangling strings. The opt-in `verify_state_law_inventory.py`
script writes `state-law-inventory-reachability.v1` artifacts with one outcome
per state, source status, content type, and content hash where fetchable. This
artifact is explicit inventory evidence and is not part of the default release
gate.

Final state-law release evidence uses `state-law-pdf-source-gate.v1` plus
`state-law-coverage.v1`. The bundle requires exactly 16 state outcomes, and
each state must be imported with a `law_id` or limited with a
`source_limitation_id` and accepted terminal state.

The fixture parser variant matrix records sampled parser coverage such as
paragraph, article-child paragraph, structural container, parse-failed, and
unsupported-format cases. Structural containers remain generated records, for
example `egbgb/art:246a` uses `unit="container"` and points to child
`egbgb/art:246a/par:1`.

## Generated Package Provenance Records

Generated packages can include `source-limitations.json` for source-level
failures. Each limitation records `limitation_id`, `source_family`,
`source_id`, `terminal_state`, `source_url`, `reason`, structured `details`,
and either `retrieved_at` or `decided_at`. Optional fields can capture HTTP
status, content type, policy reference, retryability, parser version,
jurisdiction, or adapter information. These records are provenance and coverage
evidence; they do not create fake laws or norms.

Generated `relationships.json` records are metadata-only. Supported
relationship types are `references`, `implements`, `amends`, `repeals`,
`supplements`, `same_subject_as`, `source_scope_link`, and `limitation_for`.
Subjects and objects resolve to `law`, `norm`, or `source_limitation` records
inside the package. Unresolved `external_source` targets are rejected; external
or third-party inputs may only appear as source/provenance metadata or as an
explicit source limitation. Relationship records must include provenance with a
basis and source URL, and must not copy third-party editorial text.

The release bundle validates the privacy scope seed with the relationship
policy rules, requires relationship-source metadata, and requires nonempty
relationships or source limitations. The bundle summary retains validation
status and validation errors for the relationship section.

## Source Rules

- Supported German laws use `gesetze-im-internet.de` source paths from the source matrix.
- Full GII discovery uses the official TOC, not the hand-maintained source
  matrix, as the catalog authority.
- DSGVO uses the official Publications Office / Cellar XML source for CELEX `32016R0679`, German expression `0004.02`, document `DOC_2`.
- Intentionally invalid GII paths, including `tddsg` and `pangv`, are regression checks and are not production source paths.
- Missing or invalid source metadata fails validation instead of producing partial silent data.
