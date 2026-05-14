---
type: verification
entity: source-verification
plan: "reliable-law-data-mcp"
created: "2026-05-14"
---

# Source Verification

Source probes are verified by `mcp/tests/test_source_matrix_live.py` and the Phase 1 release script.

The release gate checks representative `gesetze-im-internet.de` index URLs, known invalid alias-derived paths, and the DSGVO German Cellar `DOC_2` XML source.
