# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Render runtime law/norm dicts to Markdown for MCP resources.

Each function returns a Markdown string ready to be served as the text/
markdown payload of a Resource. The functions are pure (no I/O, no
runtime access) — they consume the dict shape produced by LegalTextRuntime
and emit human-readable Markdown with LLM-friendly structure (H1 heading,
provenance line, body, optional cross-references).
"""

from __future__ import annotations

from typing import Any


def render_norm(norm_data: dict[str, Any]) -> str:
    """Render a single norm + its provenance + related-norms links."""
    law = norm_data.get("law", {})
    norm = norm_data.get("norm", {})
    source = norm_data.get("source", {})
    related = norm_data.get("related", []) or []

    display_id = norm.get("display_id", "")
    code = law.get("display_code", "")
    title = norm.get("title", "")
    text = (norm.get("text") or "").strip()
    stand = source.get("stand_date", "—")
    retrieved = source.get("retrieved_at", "—")
    source_url = source.get("source_url", "—")

    lines = [
        f"# {display_id} {code} — {title}".rstrip(" —"),
        "",
        f"**Stand:** {stand} · **Retrieved:** {retrieved} · "
        f"**Source:** [{source_url}]({source_url if source_url != '—' else '#'})",
        "",
        text,
    ]
    if related:
        querverweise = ", ".join(r.get("canonical_id", "?") for r in related)
        lines.append("")
        lines.append(f"**Querverweise:** {querverweise}")
    return "\n".join(lines)


def render_law(law_data: dict[str, Any]) -> str:
    """Render a law's header + a clickable norm index."""
    law = law_data.get("law", {})
    norms = law_data.get("norms", []) or []

    code = law.get("display_code", "")
    display_name = law.get("display_name", "")
    stand = law.get("stand_date", "—")
    norm_count = law.get("norm_count", len(norms))
    canonical_id = law.get("canonical_id", "")

    lines = [
        f"# {code} — {display_name}",
        "",
        f"**Stand:** {stand} · **Anzahl Normen:** {norm_count}",
        "",
        "## Normen",
        "",
    ]
    for n in norms:
        norm_uri = f"legal://laws/{canonical_id}/norms/{n.get('norm_id', '')}"
        display_id = n.get("display_id", "")
        title = n.get("title", "")
        lines.append(f"- [{display_id}]({norm_uri}) {title}".rstrip())
    return "\n".join(lines)
