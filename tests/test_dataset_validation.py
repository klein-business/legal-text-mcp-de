# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.validation import validate_dataset_package, validate_norms


FIXTURE_DATASET = Path(__file__).parent / "fixtures" / "normalized"


def test_fixture_dataset_is_serving_ready():
    readiness = validate_dataset_package(FIXTURE_DATASET, stage="serving_dataset")
    assert readiness.state == "ready"
    assert NormalizedDataset.load(FIXTURE_DATASET, require_search_index=True).laws


def test_missing_search_index_is_not_serving_ready(tmp_path):
    (tmp_path / "laws.json").write_text("[]")
    (tmp_path / "norms.json").write_text("[]")
    readiness = validate_dataset_package(tmp_path, stage="serving_dataset")
    assert readiness.state == "invalid"
    assert readiness.details["search_index_status"] == "pending"


def test_duplicate_norm_ids_are_detected():
    norm = {
        "canonical_id": "bgb/par:1",
        "law_id": "bgb",
        "norm_id": "par:1",
        "unit": "par",
        "value": "1",
        "title": None,
        "text": "x",
        "status": "active",
        "url": "https://example.test",
        "source": {
            "source_kind": "gesetze-im-internet",
            "source_identifier": "bgb",
            "source_url": "https://example.test",
            "retrieved_at": "2026-05-14T00:00:00Z",
            "stand_date_status": "not_exposed",
            "content_hash": "x",
            "source_metadata": {"source_path": "bgb"},
        },
    }
    errors = validate_norms([norm, dict(norm)])
    assert any("duplicate" in error for error in errors)
