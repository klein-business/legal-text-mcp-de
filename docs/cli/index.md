# CLI reference

`legal-text-mcp-de` is a `typer`-based subcommand CLI introduced in
v2.1.0. Bare invocation prints `--help`. Add `--json` to any subcommand
for machine-readable output (matches the HTTP API response schema).

## Global flags

| Flag | Purpose |
|---|---|
| `--json` | Force JSON output even on a TTY |
| `--quiet`, `-q` | Suppress non-essential stderr |
| `--debug`, `-v` | Verbose logging |
| `--version` | Print version and exit |

## Server lifecycle

```bash
legal-text-mcp-de serve [--host H] [--port P] [--dataset PATH] [--strict]
legal-text-mcp-de http  [--host H] [--port P] [--dataset PATH]
```

## Read-only lookups

```bash
legal-text-mcp-de laws [--query Q]
legal-text-mcp-de law  CODE [--full]
legal-text-mcp-de norm CODE NORM_ID
legal-text-mcp-de cite --code CODE --unit UNIT --paragraph P [--child-unit U --child-value V]
legal-text-mcp-de search QUERY [--code C ...] [--limit N]
legal-text-mcp-de meta CODE
legal-text-mcp-de coverage
legal-text-mcp-de limitations [--source-family F] [--terminal-state S] [--state-code C] [--law-id L]
legal-text-mcp-de related CODE NORM_ID
```

## Smart tool

```bash
legal-text-mcp-de research TOPIC [--max-candidates N] [--detail brief|full]
```

Needs `ANTHROPIC_API_KEY` for full LLM-ranked synthesis. Without the key,
degrades gracefully to a ranked search-hits fallback (exit code 0).

## Corpus lifecycle

```bash
legal-text-mcp-de corpus pull   [--version V]
legal-text-mcp-de corpus verify [--cert-identity ID]
legal-text-mcp-de corpus info
```

## Diagnostics

```bash
legal-text-mcp-de health  [--url URL]
legal-text-mcp-de version
legal-text-mcp-de completion show    {bash|zsh|fish}
legal-text-mcp-de completion install {bash|zsh|fish}
```

## Exit codes

| Code | Meaning |
|---|---|
| 0 | Success |
| 1 | Runtime / business error (LegalTextError) |
| 2 | CLI usage error (typer default) |
| 3 | Smart-tool sampling error (hard) |
| 4 | Corpus error (pull or verify failed) |
| 5 | Connectivity error (`health` unreachable) |
| 130 | SIGINT |

## See also

- [HTTP API overview](../api/index.md)
- [Migration v1 → v2 → v2.1](../operations/migration-v1-v2.md)
- [Production deployment](../operations/production-deployment.md)
