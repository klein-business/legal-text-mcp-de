# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from legal_text_mcp_de.sampling.schemas import (
    RankingEntry,
    RankingResult,
    SampleResult,
)


def test_sample_result_holds_typed_payload():
    r = SampleResult(content="x", raw="x", tokens_used=42, model_used="haiku")
    assert r.tokens_used == 42


def test_ranking_result_top_n_returns_highest_scores_first():
    rr = RankingResult(
        ranking=[
            RankingEntry(norm_id="a", score=8.0, reason="moderate"),
            RankingEntry(norm_id="b", score=10.0, reason="strong"),
            RankingEntry(norm_id="c", score=5.0, reason="weak"),
        ]
    )
    top2 = rr.top_n(2)
    assert [e.norm_id for e in top2] == ["b", "a"]
