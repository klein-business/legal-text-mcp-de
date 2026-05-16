# Provenance

Every law and norm record carries provenance metadata so consumers
know exactly where the text came from and when.

## What is recorded

- **Source URL** — the original location on
  `gesetze-im-internet.de` or `publications.europa.eu`.
- **Fetch timestamp** — when the runtime saw these exact bytes.
- **Content hash** — SHA-256 of the source payload.
- **Parser path** — which normalization branch produced this norm
  record.
- **Terminal state** in the manifest — `imported`, `parse_failed`,
  etc.

## Why it matters

Provenance lets downstream tooling (and legal reviewers) verify:

- The text was fetched from an official source, not a third party.
- No editorial transformation beyond documented normalization steps.
- Stale data can be detected by re-fetching and comparing hashes.

## Data-source reuse position

| Source | Reuse |
| --- | --- |
| `gesetze-im-internet.de` | Public-domain-equivalent under §5 (1) UrhG |
| EUR-Lex / Cellar | Reuse permitted under Commission Decision 2011/833/EU with attribution |

These positions are recorded in [NOTICE](https://github.com/klein-business/legal-text-mcp-de/blob/main/NOTICE).

## Terminal states

Each source entry in the manifest is closed with exactly one terminal
state:

| State | Meaning |
| --- | --- |
| `imported` | Text fetched, parsed, and normalized successfully. |
| `unsupported_format` | Source exists but cannot be parsed by the current pipeline. |
| `source_unavailable` | Source URL returned an error or was unreachable at fetch time. |
| `parse_failed` | Fetch succeeded but the parser raised an error on the content. |
| `excluded_by_policy` | Source explicitly excluded (scope, licence, or editorial reasons). |

## Accessing provenance

Via MCP:

```python
result = mcp_client.call_tool("get_source_metadata", {"code": "bgb"})
# Returns source URL, fetch timestamp, content hash for the BGB.
```

Via HTTP API:

```bash
curl http://localhost:8080/laws/bgb | jq '.provenance'
```

## Related

- [`get_source_metadata`](../tools/get_source_metadata.md) — full provenance for a law.
- [`get_source_limitations`](../tools/get_source_limitations.md) — limitations by terminal state.
- [Data modes](data-modes.md) — fixture vs. generated corpus.
