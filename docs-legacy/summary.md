---
type: legacy
entity: docs-archive-summary
created: "2026-05-14"
---

# Legacy Documentation Archive Summary

This directory contains legacy documentation collected from the repository to establish a clean state before generating new `docs/` and `plans/`.

## Notes

- The archive is intentionally **flat** and intended for forensic reference.
- Paths in the table capture original locations.
- Time buckets are best-effort and may be inaccurate.
- `README*` files were included intentionally for this run because the root README was regenerated as canonical project documentation.

## Inventory

| Archive Path | Original Path | Module Origin (draft) | Type (draft) | Last Commit Date | Time Bucket | 3-Sentence Summary |
|-------------|---------------|------------------------|--------------|------------------|------------|--------------------|
| docs-legacy/root--README.md | README.md | root | doc | 2025-12-20 | recent | Describes the Deutsche Gesetze MCP server, its available MCP tools, and the expected law Markdown format. Covers local, Docker, and test usage plus environment variable configuration. Also mentions the data preparation script and the Google ADK example agent. |
| docs-legacy/google-adk-agent--README.md | google-adk-agent/README.md | google-adk-agent | doc | 2025-12-19 | recent | Describes the Google ADK demo agent that connects to the MCP server. Covers prerequisites, `MCP_URL`, `GEMINI_API_KEY`, and `adk web` startup. Includes a short explanation of the agent code and screenshot reference. |
