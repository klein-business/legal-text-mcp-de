# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from legal_text_mcp_de.tools.research_models import RankedNorm, ResearchReport


def test_research_report_serialises_to_dict():
    r = ResearchReport(
        topic="Test",
        top_norms=[RankedNorm(canonical_id="bgb/par:1", title="t", relevance_score=9.0)],
        synthesis="ok",
        candidates_examined=5,
        sampling_calls=2,
        status="ok",
    )
    d = r.model_dump()
    assert d["topic"] == "Test"
    assert d["top_norms"][0]["canonical_id"] == "bgb/par:1"


def test_research_report_rejects_unknown_field():
    import pytest
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        ResearchReport(topic="t", unknown_field="x")
