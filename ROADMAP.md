# Roadmap

This file captures the high-level direction for the next 3–6 months.
Tactical work is tracked in GitHub Issues with the `roadmap` label.

## Recently shipped

- v1.0.0 (target) — initial public release with eight CI workflows,
  signed PyPI + GHCR artefacts, SBOMs and SLSA-3 provenance, versioned
  documentation site, and the Tier-C quality bar.

## Planned (next 3 months)

- **Full state-law corpus coverage.** Expand the runtime to ingest
  every state-level data-protection law in the 16 German Länder with
  terminal-state tracking and source-limitation reporting.
- **Additional EU acts.** Add coverage for the AI Act, Data Act, and
  selected EU neighbour acts as imported records or limited official
  records.
- **Mypy strict ratchet completion.** Move the remaining `mcp/`
  modules from plain mypy to strict.
- **Distroless container migration.** Replace `python:3.12-slim` with
  a distroless base for the production image (the current `:slim`
  image is fine for v1.0.0; this is a hardening step for v1.x).

## Planned (3–6 months)

- **Performance work.** Profile the search and citation-resolution
  paths under realistic corpus sizes; tune as needed.
- **OpenSSF Best Practices gold.** Apply the additional controls
  required to move from silver to gold.
- **MCP-spec conformance tests.** Add a conformance suite that
  exercises the tools against the upstream MCP specification.

## Not planned

- Multi-language documentation (English-only at v1.0.0).
- A SaaS hosted offering.
- Editorial legal-text content bundling.

Roadmap proposals: open a GitHub Discussion or an issue with the
`roadmap` label.
