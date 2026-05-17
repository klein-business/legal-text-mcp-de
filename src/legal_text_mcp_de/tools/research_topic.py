# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""research_topic — multi-step legal research smart tool.

Workflow (5 steps, 2 sampling calls in full mode):
1. Corpus full-text search via runtime.search_laws.
2. Hydrate full norm text via runtime.get_norm for each candidate.
3. Sampling call 1: LLM ranks candidates by relevance.
4. Load related-norm graph via runtime.get_related_norms.
5. Sampling call 2: LLM synthesises a structured research report.

When the client lacks sampling support, returns a degraded report with
the ranked candidates only.
"""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import Context, FastMCP

from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.sampling.client import safe_sample
from legal_text_mcp_de.sampling.errors import SamplingError
from legal_text_mcp_de.sampling.schemas import RankingResult
from legal_text_mcp_de.tools.research_models import RankedNorm, ResearchReport
from legal_text_mcp_de.tools.research_prompts import (
    build_ranking_prompt,
    build_synthesis_prompt,
)


_SYSTEM = "Du bist ein deutscher juristischer Recherche-Assistent."


def register_research_topic(app: FastMCP, runtime: LegalTextRuntime) -> None:
    @app.tool()
    async def research_topic(
        topic: str,
        max_candidates: int = 20,
        detail_level: Literal["brief", "full"] = "full",
        ctx: "Context[Any, Any, Any] | None" = None,
    ) -> dict[str, Any]:
        """Multi-step legal research with LLM-assisted ranking + synthesis."""
        return (await _run_research(runtime, topic, max_candidates, detail_level, ctx)).model_dump()


async def _run_research(
    runtime: LegalTextRuntime,
    topic: str,
    max_candidates: int,
    detail_level: str,
    ctx: "Context[Any, Any, Any] | None",
) -> ResearchReport:
    # Step 1: search
    if ctx:
        await _report(ctx, 0.1, f"Searching corpus for '{topic}'...")
    try:
        search_result = runtime.search_laws(topic, None)
    except Exception as exc:
        return ResearchReport(topic=topic, status="error", note=f"search failed: {exc}")

    # search_laws returns {"query":…, "codes":…, "results": […], "count":…}
    candidates = search_result.get("results", search_result.get("hits", []))[:max_candidates]
    if not candidates:
        return ResearchReport(topic=topic, status="no_matches")

    # Step 2: hydrate norms
    if ctx:
        await _report(ctx, 0.3, f"Loading {len(candidates)} candidate norms...")
    norms = []
    for c in candidates:
        try:
            law_id = c.get("law_id") or ""
            norm_id = c.get("norm_id") or ""
            if not law_id or not norm_id:
                # fall back to splitting canonical_id
                canonical = c.get("canonical_id", "")
                if "/" in canonical:
                    law_id, norm_id = canonical.split("/", 1)
            if not law_id or not norm_id:
                continue
            full = runtime.get_norm(law_id, norm_id)
            norms.append(full)
        except Exception:
            continue
    if not norms:
        return ResearchReport(topic=topic, status="no_matches", candidates_examined=len(candidates))

    # Step 3: check sampling support
    supports = ctx is not None and getattr(ctx, "client_supports_sampling", lambda: True)()
    if not supports:
        # Degraded mode: return raw norms as RankedNorm with equal scores
        ranked = [
            RankedNorm(
                canonical_id=n.get("canonical_id", ""),
                title=(n.get("norm", {}) or {}).get("title", ""),
                relevance_score=5.0,
            )
            for n in norms[:5]
        ]
        return ResearchReport(
            topic=topic,
            top_norms=ranked,
            candidates_examined=len(candidates),
            status="degraded_no_sampling",
            note="Client lacks sampling support; returning raw search results.",
        )

    # Step 3 (real): sampling call 1 — ranking
    if ctx:
        await _report(ctx, 0.5, "Ranking norms by relevance via LLM...")
    try:
        ranking_result = await safe_sample(
            ctx,
            system=_SYSTEM,
            user_message=build_ranking_prompt(topic, norms),
            schema=RankingResult,
            max_tokens=1500,
        )
        top_n_entries = ranking_result.content.top_n(5)
    except SamplingError as exc:
        return ResearchReport(
            topic=topic,
            candidates_examined=len(candidates),
            status="error",
            note=f"ranking sampling failed: {exc}",
        )

    # Map ranked norm_ids back to full norm dicts
    norm_by_id = {n.get("canonical_id", ""): n for n in norms}
    top_norm_dicts = [norm_by_id.get(e.norm_id, {}) for e in top_n_entries]
    top_ranked = [
        RankedNorm(
            canonical_id=e.norm_id,
            title=(norm_by_id.get(e.norm_id, {}).get("norm", {}) or {}).get("title", ""),
            relevance_score=e.score,
        )
        for e in top_n_entries
    ]

    # Step 4: related norms
    if ctx:
        await _report(ctx, 0.7, "Loading related-norms graph...")
    related: dict[str, list[dict[str, Any]]] = {}
    for r in top_ranked:
        try:
            parts = r.canonical_id.split("/", 1)
            if len(parts) == 2:
                rel = runtime.get_related_norms(parts[0], parts[1])
                related[r.canonical_id] = rel.get("related", [])
        except Exception:
            continue

    # Step 5: synthesis
    synthesis_text: str | None = None
    sampling_calls = 1
    if detail_level == "full":
        if ctx:
            await _report(ctx, 0.9, "Synthesising research summary...")
        try:
            synthesis_result = await safe_sample(
                ctx,
                system=_SYSTEM,
                user_message=build_synthesis_prompt(topic, [n.model_dump() for n in top_ranked], related),
                max_tokens=2000,
            )
            synthesis_text = str(synthesis_result.content)
            sampling_calls = 2
        except SamplingError as exc:
            synthesis_text = f"[synthesis failed: {exc}]"

    provenance = [{"canonical_id": n.get("canonical_id"), "source": n.get("source", {})} for n in top_norm_dicts]

    return ResearchReport(
        topic=topic,
        top_norms=top_ranked,
        related_norms=related,
        synthesis=synthesis_text,
        candidates_examined=len(candidates),
        sampling_calls=sampling_calls,
        provenance=provenance,
        status="ok",
    )


async def _report(ctx: "Context[Any, Any, Any]", fraction: float, message: str) -> None:
    """Best-effort progress reporting; never raise."""
    try:
        await ctx.report_progress(fraction, total=1.0, message=message)
    except Exception:
        pass
