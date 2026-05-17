# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Prompt builders for the research_topic Smart Tool."""

from __future__ import annotations

import json
from typing import Any


def build_ranking_prompt(topic: str, norms: list[dict[str, Any]]) -> str:
    """Ask the LLM to rank each norm by relevance to the topic.

    Returns a prompt expecting a JSON response matching RankingResult.
    """
    norm_blurbs = []
    for n in norms:
        law = n.get("law", {}).get("display_code", "?")
        nid = n.get("canonical_id") or f"{law.lower()}/{n.get('norm', {}).get('norm_id', '?')}"
        title = n.get("norm", {}).get("title", "")
        text = (n.get("norm", {}).get("text") or "")[:300]
        norm_blurbs.append(f"- canonical_id: {nid}\n  title: {title}\n  excerpt: {text}")
    norms_text = "\n\n".join(norm_blurbs)
    return (
        f"Du bist ein juristischer Recherche-Assistent.\n\n"
        f"Thema: {topic}\n\n"
        f"Bewerte die Relevanz der folgenden Normen für das Thema. "
        f"Antworte NUR mit JSON in genau diesem Format:\n"
        f'  {{"ranking": [{{"norm_id": "...", "score": 0-10 (float), "reason": "..."}}]}}\n\n'
        f"Normen:\n{norms_text}"
    )


def build_synthesis_prompt(
    topic: str,
    top_norms: list[dict[str, Any]],
    related: dict[str, list[dict[str, Any]]],
) -> str:
    """Ask the LLM to synthesise a research summary."""
    norm_section = json.dumps(top_norms, ensure_ascii=False, indent=2)
    related_section = json.dumps(related, ensure_ascii=False, indent=2)
    return (
        f"Du bist ein juristischer Recherche-Assistent.\n\n"
        f"Thema: {topic}\n\n"
        f"Top-Normen:\n{norm_section}\n\n"
        f"Beziehungs-Normen:\n{related_section}\n\n"
        f"Erstelle eine strukturierte Recherche-Synthese (max. 8 Sätze) die zeigt, "
        f"wie diese Normen auf das Thema anwendbar sind. Zitiere die canonical_id "
        f"jeder Norm. Sprache: deutsch."
    )
