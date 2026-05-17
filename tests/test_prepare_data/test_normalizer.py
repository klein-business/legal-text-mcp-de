# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from prepare_data.normalizer import normalize_for_runtime
from prepare_data.state_law.base import NormalizedLaw, NormalizedNorm


def test_normalize_state_law_into_runtime_format():
    by_law = NormalizedLaw(
        canonical_id="by/baybo",
        display_code="BayBO",
        display_name="Bayerische Bauordnung",
        state_code="by",
        source_url="https://www.gesetze-bayern.de/Content/Document/BayBO",
        norms=(NormalizedNorm(norm_id="art-1", title="Geltungsbereich", text="Dieses Gesetz gilt …"),),
    )
    out = normalize_for_runtime([by_law], source_kind="state-bayern", retrieved_at="2026-05-17T00:00:00Z")
    assert len(out) == 1
    law_dict = out[0]
    assert law_dict["canonical_id"] == "by/baybo"
    assert law_dict["display_code"] == "BayBO"
    assert law_dict["source"]["source_kind"] == "state-bayern"
    assert law_dict["source"]["retrieved_at"] == "2026-05-17T00:00:00Z"
    assert law_dict["source"]["source_identifier"] == "by/baybo"
    assert law_dict["source"]["source_url"] == "https://www.gesetze-bayern.de/Content/Document/BayBO"
    assert len(law_dict["norms"]) == 1
    assert law_dict["norms"][0]["norm_id"] == "art-1"
    assert law_dict["norms"][0]["title"] == "Geltungsbereich"


def test_normalize_empty_input_returns_empty_list():
    assert normalize_for_runtime([], source_kind="state-bayern", retrieved_at="2026-05-17T00:00:00Z") == []


def test_normalize_preserves_norm_order():
    law = NormalizedLaw(
        canonical_id="nrw/test",
        display_code="TEST",
        display_name="Test Law",
        state_code="nrw",
        source_url="https://example.invalid",
        norms=tuple(NormalizedNorm(norm_id=f"§-{i}", title=f"T{i}", text=f"text {i}") for i in range(1, 4)),
    )
    out = normalize_for_runtime([law], source_kind="state-nrw", retrieved_at="2026-05-17T00:00:00Z")
    assert [n["norm_id"] for n in out[0]["norms"]] == ["§-1", "§-2", "§-3"]
