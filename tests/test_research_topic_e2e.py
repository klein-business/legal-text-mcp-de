# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import json

import pytest

from legal_text_mcp_de.config import settings
from legal_text_mcp_de.legal_texts.runtime import LegalTextRuntime
from legal_text_mcp_de.sampling.testing import MockSamplingClient
from legal_text_mcp_de.tools.research_topic import _run_research


@pytest.mark.asyncio
async def test_research_topic_full_workflow_with_mock_sampling():
    runtime = LegalTextRuntime.from_settings(settings, strict=False)
    if runtime.dataset is None:
        pytest.skip("no dataset loaded for E2E")

    ranking_json = json.dumps({"ranking": [{"norm_id": "bgb/par:355", "score": 9.5, "reason": "relevant"}]})
    synthesis_text = "Synthese: § 355 BGB regelt das Widerrufsrecht …"
    ctx = MockSamplingClient(responses=[ranking_json, synthesis_text])

    report = await _run_research(
        runtime,
        topic="Verbraucherwiderruf",
        max_candidates=10,
        detail_level="full",
        ctx=ctx,
    )
    assert report.status in {"ok", "no_matches"}
    if report.status == "ok":
        assert report.sampling_calls >= 1


@pytest.mark.asyncio
async def test_research_topic_degrades_when_no_sampling():
    runtime = LegalTextRuntime.from_settings(settings, strict=False)
    if runtime.dataset is None:
        pytest.skip("no dataset loaded for E2E")

    ctx = MockSamplingClient(responses=[], supports_sampling=False)
    report = await _run_research(
        runtime,
        topic="Verbraucherwiderruf",
        max_candidates=10,
        detail_level="brief",
        ctx=ctx,
    )
    assert report.status in {"degraded_no_sampling", "no_matches"}
