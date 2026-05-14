---
type: planning
entity: implementation-plan
plan: "reliable-law-data-mcp"
phase: 1
status: draft
created: "2026-05-14"
updated: "2026-05-14"
---

# Implementation Plan: Phase 1 - Domain Contracts and Dataset Layout

> Implements [Phase 1](../phases/phase-1.md) of [reliable-law-data-mcp](../plan.md)

## Approach

Phase 1 is a contract and planning-artifact phase. It should not change runtime code. The implementation work is to finalize repository-visible contract artifacts under `plans/reliable-law-data-mcp/`, verify them against current code/docs and live source probes already captured in the source matrix, and make sure later implementation phases can use those artifacts without inventing source paths, identifier grammar, fixture coverage, or error semantics.

## Affected Modules

| Module | Change Type | Description |
|--------|-------------|-------------|
| [mcp-server](../../../docs/modules/mcp-server.md) | reference only | Current parser/server limitations are used as code anchors; no runtime code change in this phase. |
| Plan artifacts | modify/create | Finalize `contracts.md`, `source-matrix.md`, `fixture-inventory.md`, `plan.md`, `phases/phase-*.md`, and `todo.md` as implementation-ready contracts. |

## Required Context

| File | Why |
|------|-----|
| `plans/reliable-law-data-mcp/plan.md` | Global requirements, DoD, test strategy, and phase order. |
| `plans/reliable-law-data-mcp/phases/phase-1.md` | Gated Phase 1 scope and acceptance criteria. |
| `plans/reliable-law-data-mcp/contracts.md` | Shared identifier, resolver, error, readiness, MCP migration, and search score contracts. |
| `plans/reliable-law-data-mcp/source-matrix.md` | Canonical source paths, URLs, probe expectations, and invalid-path regression requirements. |
| `plans/reliable-law-data-mcp/fixture-inventory.md` | Minimum fixture and golden JSON inventory for later phases. |
| `docs/overview.md` | High-level architecture and current development/test commands for orientation. |
| `docs/modules/mcp-server.md` | Current code inventory and limitations that contracts must address. |
| `docs/features/law-loading-and-indexing.md` | Current source-loading behavior and known data-loading gaps. |
| `docs/features/mcp-law-tools.md` | Current MCP tool behavior, double serialization, and error-contract gaps. |
| `mcp/config.py` | Current settings still default to `/app/gesetze/`, which later phases must replace. |
| `mcp/parser.py` | Current parser and library behavior provide grounding for migration contracts. |
| `mcp/server.py` | Current MCP tool names and return shapes provide grounding for MCP migration contracts. |
| `Dockerfile` | Current image clones `bundestag/gesetze`, which later phases must remove. |

## Implementation Steps

### Step 1: Finalize Source Matrix

- **What**: Ensure `source-matrix.md` lists every Phase 1 source with canonical ID, display code, aliases, source kind, upstream path or identifier, URL(s), expected probe status, and known invalid paths.
- **Where**: `plans/reliable-law-data-mcp/source-matrix.md`.
- **Why**: Later import and registry work must not infer source paths from display codes or aliases.
- **Considerations**: Keep TDDDG source path as `ttdsg`; keep PAngV source path as `pangv_2022`; keep DSGVO as `eur-lex-cellar` with the retrievable Cellar XML URL, not the EUR-Lex `TXT` page.

### Step 2: Finalize Fixture Inventory

- **What**: Ensure `fixture-inventory.md` enumerates exact required citations and transport coverage expectations, including concrete BDSG and DSGVO fixtures.
- **Where**: `plans/reliable-law-data-mcp/fixture-inventory.md`.
- **Why**: Later phases need exact fixtures for parser, resolver, search, MCP, HTTP, and release-gate tests.
- **Considerations**: Preserve the EGBGB `Art. 246a` container plus `Art. 246a § 1` child distinction.

### Step 3: Finalize Shared Contracts

- **What**: Ensure `contracts.md` defines canonical IDs, article-plus-section request grammar, HTTP norm path encoding, structured error payloads, readiness states, MCP migration decision, and normalized search score semantics.
- **Where**: `plans/reliable-law-data-mcp/contracts.md`.
- **Why**: This prevents each implementation phase from inventing incompatible API and data contracts.
- **Considerations**: The resolver signature must include `child_unit` and `child_value`; HTTP must encode child norm paths as one segment such as `art%3A246a%2Fpar%3A1`.

### Step 4: Finalize Domain Schemas and Dataset Layout

- **What**: Ensure `contracts.md` contains concrete logical schemas for law records, source metadata, raw snapshots, normalized norms, subdivisions, manifests, citation requests/responses, search results, and structured errors.
- **Where**: `plans/reliable-law-data-mcp/contracts.md`.
- **Why**: Phase 1 explicitly requires domain records and data layout contracts; later import, parser, resolver, search, MCP, and HTTP phases need these fields pinned.
- **Considerations**: Include required/optional/known-issue-capable field classifications and the raw/normalized/fixture/golden dataset paths.

### Step 5: Align Phase Docs and Todo

- **What**: Make sure Phase 1 through Phase 9 docs reference the support artifacts where they depend on them, and `todo.md` tracks the Phase 1 contract tasks.
- **Where**: `plans/reliable-law-data-mcp/plan.md`, `plans/reliable-law-data-mcp/phases/phase-1.md`, `plans/reliable-law-data-mcp/phases/phase-2.md`, `plans/reliable-law-data-mcp/phases/phase-4.md`, `plans/reliable-law-data-mcp/phases/phase-5.md`, `plans/reliable-law-data-mcp/phases/phase-6.md`, `plans/reliable-law-data-mcp/phases/phase-7.md`, `plans/reliable-law-data-mcp/phases/phase-8.md`, `plans/reliable-law-data-mcp/phases/phase-9.md`, and `plans/reliable-law-data-mcp/todo.md`.
- **Why**: Later phase implementation plans should reference the same contract artifacts and acceptance criteria.
- **Considerations**: Phase 3 already depends on source-matrix/registry semantics; do not add implementation details beyond accepted scope. Keep changelog append-only.

### Step 6: Validate Plan Artifact Integrity

- **What**: Run link checks, heading/schema checks, todo/status stale-phrase checks, and source URL probe checks for the active contract and implementation artifacts.
- **Where**: `plans/reliable-law-data-mcp/**`.
- **Why**: Phase 1 is complete only if later agents can navigate and trust the artifacts.
- **Considerations**: Use local link checks for Markdown references; use HTTP status probes for matrix URLs that are part of the contract. Placeholder checks must ignore fenced code blocks and historical review artifacts so the verifier does not fail on quoted examples. The todo context must reference the existing implementation plan, not a "to be created" placeholder.

## Testing Plan

Primary verify command:

```bash
python3 - <<'PY'
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request

root = Path('plans/reliable-law-data-mcp')
files = [
    file
    for file in root.rglob('*.md')
    if 'reviews' not in file.relative_to(root).parts
]
missing = []
required_headings = {
    'contracts.md': [
        '## Dataset Layout',
        '## Field Classification',
        '## Domain Record Schemas',
        '### LawRecord',
        '### SourceMetadata',
        '### RawSnapshotRecord',
        '### NormRecord',
        '### SubdivisionRecord',
        '### ManifestRecord',
        '### CitationRequest',
        '### CitationResponse',
        '### SearchResult',
        '## Structured Error Payload',
        '## Dataset Readiness Contract',
    ],
    'source-matrix.md': [
        '## German Laws: gesetze-im-internet.de',
        '## EU Law: EUR-Lex',
        '## Source Validation Requirements',
    ],
    'fixture-inventory.md': [
        '## Required Citation Fixtures',
        '## Golden JSON Requirements',
        '## Regression Fixtures',
    ],
}

def strip_fenced(text: str) -> str:
    return re.sub(r'```.*?```', '', text, flags=re.S)

for file in files:
    text = file.read_text()
    prose = strip_fenced(text)
    if '{' + '{' in prose or '}' + '}' in prose:
        missing.append((str(file), 'unresolved template placeholder'))
    for match in re.finditer(r'!?' + r'\\[[^\\]]+\\]\\(([^)]+)\\)', prose):
        target = match.group(1).split('#', 1)[0]
        if not target or '://' in target or target.startswith('mailto:'):
            continue
        if not (file.parent / target).resolve().exists():
            missing.append((str(file), target))
required = [
    root / 'contracts.md',
    root / 'source-matrix.md',
    root / 'fixture-inventory.md',
    root / 'phases/phase-1.md',
]
for path in required:
    if not path.exists():
        missing.append((str(path), 'required artifact missing'))
for rel, headings in required_headings.items():
    text = (root / rel).read_text()
    for heading in headings:
        if heading not in text:
            missing.append((str(root / rel), f'missing heading {heading}'))
todo_text = (root / 'todo.md').read_text()
if 'to be created' in todo_text:
    missing.append((str(root / 'todo.md'), 'stale implementation-plan placeholder'))
if '[Phase 1 Implementation Plan](implementation/phase-1-impl.md)' not in todo_text:
    missing.append((str(root / 'todo.md'), 'missing Phase 1 implementation plan link'))

probes = [
    ('https://www.gesetze-im-internet.de/bgb/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/bgb/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/bgbeg/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/bgbeg/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/ddg/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/ddg/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/uwg_2004/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/uwg_2004/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/ttdsg/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/ttdsg/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/bdsg_2018/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/bdsg_2018/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/bfsg/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/bfsg/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/vsbg/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/vsbg/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/pangv_2022/index.html', 200, None),
    ('https://www.gesetze-im-internet.de/pangv_2022/xml.zip', 200, None),
    ('https://www.gesetze-im-internet.de/tddsg/index.html', 404, None),
    ('https://www.gesetze-im-internet.de/pangv/index.html', 404, None),
    ('https://publications.europa.eu/resource/cellar/3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02/DOC_2', 200, 'xml'),
]
for url, expected_status, content_hint in probes:
    req = urllib.request.Request(url, headers={'User-Agent': 'legal-text-mcp-de-plan-check/1.0'})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            status = resp.status
            content_type = resp.headers.get('content-type', '').lower()
    except urllib.error.HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get('content-type', '').lower()
    if status != expected_status:
        missing.append((url, f'expected HTTP {expected_status}, got {status}'))
    if content_hint and content_hint not in content_type:
        missing.append((url, f'expected content-type containing {content_hint}, got {content_type}'))
    if '32016R0679' not in url and '3e485e15-11bd-11e6-ba9a-01aa75ed71a1.0004.02' not in url:
        continue
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            body = resp.read(4096).decode('utf-8', errors='replace')
    except urllib.error.HTTPError as exc:
        body = exc.read(4096).decode('utf-8', errors='replace')
    if '<LG.DOC>DE</LG.DOC>' not in body:
        missing.append((url, 'expected German DSGVO XML with <LG.DOC>DE</LG.DOC>'))
    if '<ACT' not in body:
        missing.append((url, 'expected article-bearing DSGVO act XML with <ACT'))

if missing:
    for file, issue in missing:
        print(f'FAIL {file}: {issue}')
    sys.exit(1)
print(f'Checked {len(files)} plan markdown files and {len(probes)} source probes; contracts OK.')
PY
```

| Test Type | What to Test | Expected Outcome |
|-----------|-------------|-----------------|
| Contract integrity | Required support artifacts exist and contain no unresolved template placeholders. | Command exits 0. |
| Link validation | Internal Markdown links across plan artifacts resolve. | Command exits 0. |
| Todo/status alignment | `todo.md` links the existing Phase 1 implementation plan and contains no stale "to be created" placeholder. | Command exits 0. |
| Schema/layout coverage | `contracts.md` contains required domain schema and dataset layout sections. | Command exits 0. |
| Source matrix probes | Valid URLs return expected 200 status, invalid paths return expected 404, and DSGVO Cellar URL returns XML. | Command exits 0. |

### Test Integrity Constraints

- Existing runtime tests under `mcp/tests/` are not affected by Phase 1 because no runtime code changes are made.
- Existing tests must not be disabled, deleted, or weakened.
- Phase 1 verification does not replace later parser/import/resolver tests; it only validates planning contract artifacts.

## Rollback Strategy

Revert changes under `plans/reliable-law-data-mcp/contracts.md`, `source-matrix.md`, `fixture-inventory.md`, `plan.md`, `phases/`, and `todo.md`. No runtime code or data files are affected by this phase.

## Open Decisions

| Decision | Options | Chosen | Rationale |
|----------|---------|--------|-----------|
| DSGVO source | EUR-Lex `TXT` page / Publications Office Cellar XML / committed manual fixture | Publications Office Cellar XML | The Cellar XML URL is machine-retrievable and avoids the EUR-Lex HTTP 202 challenge observed in this environment. |
| EGBGB `Art. 246a` behavior | aggregate child text / container only / invalid without child | Container plus child references; `Art. 246a § 1` is text-bearing | This matches observed `gesetze-im-internet.de` structure and avoids fabricated aggregate text. |
| Legacy MCP tools | keep stable / temporary aliases / remove stable surface | Remove stable surface | Phase 1 is a breaking API cleanup; temporary aliases must be gone by release gate. |

## Reality Check

### Code Anchors Used

| File | Symbol/Area | Why it matters |
|------|-------------|----------------|
| `mcp/config.py` | `Settings.load_from_folder` | Current runtime default points to `/app/gesetze/`, which later phases must replace. |
| `mcp/parser.py` | `LawParser`, `LawLibrary` | Current parser handles Markdown paragraphs only and does not support the new normalized contracts. |
| `mcp/server.py` | `get_lawlibrary`, `get_paragraph`, `search_laws` | Current MCP API uses old tool names and stringified JSON. |
| `Dockerfile` | `RUN git clone https://github.com/bundestag/gesetze.git` | Current container packages demo data and must be changed in a later phase. |
| `docs/features/mcp-law-tools.md` | Edge Cases & Limitations | Documents double JSON serialization and missing structured errors. |

### Mismatches / Notes

- Phase 1 intentionally does not fix runtime code; it locks contracts so Phases 2-8 can make targeted code changes.
- The contracts deliberately treat DSGVO as `eur-lex-cellar`, separate from the German `gesetze-im-internet` import path.
