---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 3
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 3 - Canonical Registry and Alias Resolution

> Implements [Phase 3](../phases/phase-3.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 3 introduces a versioned, data-owned law registry that resolves user-facing aliases to canonical law IDs, source identifiers, and display codes. The registry should be independent from the legacy Markdown parser and should consume or mirror the Phase 2 source specs rather than re-infer source paths from aliases. The implementation adds registry data, typed loader/validator behavior, resolver APIs, structured ambiguity/unknown-law errors, and focused unit tests for all required Phase 1 laws.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| `mcp/legal_texts/registry.py` | create | Registry loader, validation, alias normalization, resolution, suggestions, and collision checks. |
| `mcp/legal_texts/models.py` | modify | Add law registry records or reuse existing `LawRecord` fields from Phase 1 contracts. |
| `mcp/legal_texts/errors.py` | modify | Add/verify `LAW_NOT_FOUND` and `AMBIGUOUS_LAW_ALIAS` structured errors. |
| `mcp/legal_texts/sources.py` | modify/reference | Use Phase 2 source specs as the source-path/source-kind truth table. |
| `mcp/legal_texts/data/laws.v1.json` | create | Versioned registry artifact with canonical IDs, display names, display codes, aliases, source kind, and source identifier/path. |
| `mcp/tests/test_registry.py` | create | Alias mapping, canonical lookup, source path separation, suggestion, ambiguity, and collision validation tests. |
| `docs/features/law-loading-and-indexing.md` | modify | Document canonical registry behavior and its boundary with current runtime loading. |
| `docs/modules/mcp-server.md` | modify/reference | Note the new registry module as shared domain infrastructure while legacy parser storage remains until later phases. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global alias, canonical ID, response metadata, and collision requirements. |
| `plans/reliable-law-data-mcp/phases/phase-3.md` | Gated registry scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | Canonical identifier grammar, law record fields, source path rules, and error payloads. |
| `plans/reliable-law-data-mcp/source-matrix.md` | Authoritative Phase 1 law IDs, aliases, display codes, source kinds, source paths, and DSGVO source identifier. |
| `plans/reliable-law-data-mcp/implementation/phase-2-impl.md` | Source spec and source metadata decisions that Phase 3 must align with. |
| `mcp/tests/fixtures/source_matrix_expected.json` | Independent Phase 2 oracle for source IDs, URLs, source identifiers, and invalid path probes. |
| `docs/overview.md` | Project structure and test command context. |
| `docs/features/law-loading-and-indexing.md` | Current runtime still keys laws by parsed Markdown `jurabk`; registry is new shared domain infrastructure. |
| `mcp/parser.py` | Existing implicit code lookup behavior to avoid modifying in Phase 3 except by future integration. |
| `mcp/tests/conftest.py` | Existing pytest style and fixtures. |

## Registry Contract

The registry artifact must be data, not parser logic. Each law entry includes:

- `registry_version`: registry-level version string, initially `1`.
- `canonical_id`: one of `bgb`, `egbgb`, `ddg`, `uwg_2004`, `tdddg`, `bdsg_2018`, `bfsg`, `vsbg`, `pangv_2022`, or `dsgvo_eu_2016_679`.
- `display_code` and `display_name`.
- `source_kind`.
- `source_identifier`; German laws use the exact source path. DSGVO must use the exact string `CELEX:32016R0679`.
- `source_metadata`; German laws include `source_path`; DSGVO mirrors Phase 2 metadata with `celex="32016R0679"`, `cellar_work="3e485e15-11bd-11e6-ba9a-01aa75ed71a1"`, `expression="0004.02"`, `language="DE"`, and `document="DOC_2"`.
- `aliases`: versioned alias records with `value`, `normalized`, `valid_from` optional, `valid_to` optional, and `note` optional.

Alias normalization must be deterministic:

- trim leading/trailing whitespace;
- casefold for case-insensitive matching;
- normalize Unicode to a stable form;
- collapse repeated internal whitespace;
- keep source-path-relevant underscores and digits intact;
- support German umlaut aliases and ASCII fallback aliases listed in `source-matrix.md`.

Every alias in every `Required Aliases` cell of `source-matrix.md` is a required resolver test case:

| Canonical ID | Aliases Required In Table-Driven Tests |
|--------------|----------------------------------------|
| `bgb` | `BGB`, `bgb`, `Buergerliches Gesetzbuch`, `Bürgerliches Gesetzbuch` |
| `egbgb` | `EGBGB`, `BGBEG`, `bgbeg`, `Einführungsgesetz zum Bürgerlichen Gesetzbuche` |
| `ddg` | `DDG`, `ddg`, `Digitale-Dienste-Gesetz` |
| `uwg_2004` | `UWG`, `uwg_2004`, `Gesetz gegen den unlauteren Wettbewerb` |
| `tdddg` | `TDDDG`, `TTDSG`, `ttdsg`, `tddsg`, `Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz` |
| `bdsg_2018` | `BDSG`, `bdsg_2018`, `Bundesdatenschutzgesetz` |
| `bfsg` | `BFSG`, `bfsg`, `Barrierefreiheitsstärkungsgesetz`, `Barrierefreiheitsstaerkungsgesetz` |
| `vsbg` | `VSBG`, `vsbg`, `Verbraucherstreitbeilegungsgesetz` |
| `pangv_2022` | `PAngV`, `pangv`, `pangv_2022`, `Preisangabenverordnung` |
| `dsgvo_eu_2016_679` | `DSGVO`, `GDPR`, `Datenschutz-Grundverordnung`, `Verordnung (EU) 2016/679` |

Ambiguity and validation behavior must be separated:

- The default `load_registry()` path validates and rejects duplicate canonical IDs and normalized alias collisions before serving.
- `LawRegistry.from_entries(entries, validate=False)` or an equivalent explicitly named low-level constructor may exist only for tests and diagnostics.
- `resolve_law()` may return/raise `AMBIGUOUS_LAW_ALIAS` only when operating on such an explicitly non-validating registry. Production registry loading must fail earlier instead of serving ambiguous aliases.
- Tests must cover both the committed registry's fail-fast collision-free validation and the low-level ambiguous resolver error shape.

## Implementation Steps

### Step 1: Create Versioned Registry Artifact

- **What**: Add a checked registry artifact containing every Phase 1 law with canonical ID, display code, display name, source kind, source identifier/path, and versioned aliases.
- **Where**: `mcp/legal_texts/data/laws.v1.json`.
- **Why**: Alias behavior must be auditable and versioned instead of hidden in parser branches.
- **Considerations**: Include every alias listed in the Registry Contract table above, not only headline examples. Pin DSGVO `source_identifier` to `CELEX:32016R0679` and include the Cellar metadata fields in `source_metadata`.

### Step 2: Implement Registry Models and Loader

- **What**: Add registry record structures and a loader that reads the versioned artifact, builds normalized alias indexes, and exposes all laws in deterministic order.
- **Where**: `mcp/legal_texts/registry.py` and `mcp/legal_texts/models.py`.
- **Why**: Resolver, import validation, MCP, and HTTP need one law identity service.
- **Considerations**: Keep parsing based on standard `json` unless a dependency already exists. Responses should be JSON-compatible dictionaries or simple model objects with `.to_dict()` conversion.

### Step 3: Validate Source Alignment and Collisions

- **What**: Validate that registry canonical IDs, display codes, source kinds, and source identifiers match Phase 2 source specs and `source-matrix.md`; detect duplicate canonical IDs and normalized alias collisions.
- **Where**: `mcp/legal_texts/registry.py`, `mcp/legal_texts/sources.py`, and `mcp/tests/test_registry.py`.
- **Why**: Aliases like `tddsg` and `pangv` must resolve as user input but must never become upstream source paths.
- **Considerations**: Collision tests should construct an intentionally bad in-memory registry, not mutate the committed registry artifact.

### Step 4: Implement Alias Resolution and Suggestions

- **What**: Implement `resolve_law(code)` behavior returning canonical law metadata, and unknown/ambiguous handling with bounded suggestions.
- **Where**: `mcp/legal_texts/registry.py` and `mcp/legal_texts/errors.py`.
- **Why**: Later resolver, search, MCP, and HTTP code need a shared law-code resolver with controlled failure modes.
- **Considerations**: Default registry loading must fail before serving if aliases collide. `AMBIGUOUS_LAW_ALIAS` is exercised only through an explicitly non-validating low-level registry constructor used by tests/diagnostics. `LAW_NOT_FOUND` should include up to 10 suggestions.

### Step 5: Add Required Registry Tests

- **What**: Test every alias from the Registry Contract table, source path separation, canonical lookup, display code metadata, unknown-law suggestions, collision detection, ambiguity error shape, and DSGVO source identity serialization.
- **Where**: `mcp/tests/test_registry.py`.
- **Why**: Phase 3 acceptance criteria are mostly unit-level identity behavior.
- **Considerations**: Tests must be table-driven over all aliases from `source-matrix.md`. They must prove `TDDDG`, `TTDSG`, `ttdsg`, and `tddsg` resolve to canonical `tdddg` while the registry/source spec still uses upstream source path `ttdsg`; similarly `PAngV`, `pangv`, and `pangv_2022` resolve to canonical `pangv_2022` while source path is `pangv_2022`. DSGVO tests must assert `source_identifier == "CELEX:32016R0679"` plus Cellar metadata fields.

### Step 6: Document Registry Boundary

- **What**: Document that the registry is now the canonical law identity layer, while the legacy Markdown `LawLibrary` still keys loaded laws by `jurabk` until later phases integrate the registry.
- **Where**: `docs/features/law-loading-and-indexing.md` and `docs/modules/mcp-server.md`.
- **Why**: Phase 3 adds domain infrastructure without yet changing runtime MCP behavior.
- **Considerations**: Do not claim MCP tools use the registry until Phase 7 integrates them. Keep docs clear that source paths are not inferred from aliases.

## Testing Plan

Primary verify command:

```bash
PYTHONPATH=mcp python3 -m pytest mcp/tests/test_registry.py mcp/tests/test_source_matrix.py mcp/tests/test_source_import.py mcp/tests/test_parser.py mcp/tests/test_library.py
```

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Required alias mapping | Every alias from every `Required Aliases` cell in `source-matrix.md` resolves to canonical ID, display code, source kind, and source identifier. | All table-driven cases return expected metadata. |
| Source path separation | Historical aliases such as `tddsg` and `pangv` do not become source paths. | Returned law metadata uses `ttdsg` and `pangv_2022` source identifiers. |
| Registry validation | Duplicate canonical IDs and normalized alias collisions fail validation. | Structured validation errors are raised before serving. |
| Unknown law suggestions | Unknown input returns `LAW_NOT_FOUND` with bounded suggestions. | Error payload includes requested code and no more than 10 suggestions. |
| Ambiguous alias error | An intentionally bad in-memory registry created through an explicitly non-validating low-level constructor can produce `AMBIGUOUS_LAW_ALIAS`. | Error payload includes candidate suggestions and does not silently choose; normal registry loading still rejects collisions. |
| DSGVO source identity | Registry serializes DSGVO as `source_identifier="CELEX:32016R0679"` with Cellar metadata mirrored from Phase 2 source specs. | Tests fail if CELEX, Cellar work, expression `0004.02`, language `DE`, or document `DOC_2` drift. |
| Source spec alignment | Registry entries match Phase 2 source specs and `source-matrix.md`. | Tests fail if canonical IDs, source kinds, or source identifiers drift. |
| Existing import/parser/library tests | Earlier phase behavior remains passing. | Existing tests still pass. |
| Real-world boundary | Phase 3 uses deterministic registry/source-spec conformance tests only; Phase 2 live source probes remain the upstream availability gate. | No network access is required for Phase 3 completion. |

### Test Integrity Constraints

- Existing Phase 2 import/source tests must keep passing; do not weaken source path or invalid-path assertions.
- Existing parser/library tests may remain unchanged because runtime integration is deferred.
- Registry tests should use in-memory invalid registries for collision and ambiguity cases rather than editing committed registry data during tests.

## Rollback Strategy

Remove `mcp/legal_texts/registry.py`, `mcp/legal_texts/data/laws.v1.json`, registry model/error additions if unused by later phases, `mcp/tests/test_registry.py`, and registry documentation updates. Phase 2 source import code should remain intact.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| Registry format | JSON / YAML / Python constants | JSON | Standard-library readable and clearly data-owned. |
| Alias matching | exact only / normalized exact plus suggestions / fuzzy auto-select | normalized exact plus suggestions | Avoids silent wrong-law selection while helping clients recover. |
| Ambiguity in committed registry | allow and resolve by priority / fail validation / choose latest alias | fail validation | Alias collisions are unsafe for legal citations. |
| Ambiguity test path | production-invalid registry / non-validating low-level constructor / no ambiguity test | non-validating low-level constructor | Keeps production validation fail-fast while still testing the required error contract. |
| DSGVO source identifier | CELEX string / Cellar work ID / full source URL / compound object only | `CELEX:32016R0679` plus structured Cellar metadata | Gives one stable registry identifier while preserving complete source provenance from Phase 2. |
| Runtime integration | replace `LawLibrary` keys now / defer integration / dual path | defer integration | Phase 3 owns identity infrastructure; resolver/MCP integration happens in later phases. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/parser.py` | `LawParser.short_title` and `LawLibrary.laws` | Current runtime keys laws by lowercased parsed abbreviation, not by canonical registry ID. |
| `mcp/parser.py` | `LawLibrary.get_available_laws` | Current fuzzy law lookup is based on loaded law keys and `rapidfuzz`; new registry suggestions should be separate. |
| `mcp/parser.py` | `LawLibrary.get` URL construction | Existing source URLs use `law.short_title.lower()`, which is wrong for source-path/display-code mismatches and will be fixed later. |
| `plans/reliable-law-data-mcp/source-matrix.md` | Source rows | Registry must match canonical IDs, aliases, source kinds, and source paths from the matrix. |
| `plans/reliable-law-data-mcp/implementation/phase-2-impl.md` | Phase 2 source specs | Registry must align with source specs rather than duplicate conflicting source truth. |

### Mismatches / Notes

- Phase 3 does not replace `LawLibrary` lookup or MCP tool behavior yet; it creates the shared identity layer for Phases 5, 7, and 8.
- `mcp/legal_texts` is created by Phase 2; it does not exist in the pre-plan repository snapshot. Phase 3 execution must verify Phase 2 outputs before editing this package.
- The committed registry should be collision-free; ambiguity behavior is still tested with synthetic invalid registry data so transport error contracts remain covered.
- Existing legacy fuzzy lookup may continue to exist until MCP migration removes the old demo tool surface.
