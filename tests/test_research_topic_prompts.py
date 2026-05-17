# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from legal_text_mcp_de.tools.research_prompts import (
    build_ranking_prompt,
    build_synthesis_prompt,
)


def test_build_ranking_prompt_lists_each_norm():
    norms = [
        {
            "canonical_id": "bgb/par:1",
            "law": {"display_code": "BGB"},
            "norm": {"title": "x", "text": "y", "norm_id": "par:1"},
        },
        {
            "canonical_id": "bgb/par:2",
            "law": {"display_code": "BGB"},
            "norm": {"title": "a", "text": "b", "norm_id": "par:2"},
        },
    ]
    text = build_ranking_prompt("topic", norms)
    assert "topic" in text
    assert "bgb/par:1" in text
    assert "bgb/par:2" in text
    assert "JSON" in text


def test_build_synthesis_prompt_includes_topic_and_norms():
    text = build_synthesis_prompt(
        "Verbraucherwiderruf",
        [{"canonical_id": "bgb/par:355"}],
        {"par:355": [{"canonical_id": "bgb/par:312g"}]},
    )
    assert "Verbraucherwiderruf" in text
    assert "bgb/par:355" in text
    assert "bgb/par:312g" in text
    assert "deutsch" in text
