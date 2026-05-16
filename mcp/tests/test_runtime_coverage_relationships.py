# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
from pathlib import Path

from legal_texts.dataset import NormalizedDataset
from legal_texts.runtime import LegalTextRuntime


LEGACY_DATASET = Path(__file__).parent / "fixtures" / "normalized"
GENERATED_PACKAGE = Path(__file__).parent / "fixtures" / "generated_package"


def test_legacy_dataset_exposes_empty_generated_package_metadata():
    dataset = NormalizedDataset.load(LEGACY_DATASET, require_search_index=True)
    coverage = dataset.get_corpus_coverage()

    assert coverage["generated_package_present"] is False
    assert coverage["package"] == {}
    assert coverage["manifest"] == {}
    assert coverage["counts"]["source_limitations"] == 0
    assert coverage["counts"]["relationships"] == 0
    assert dataset.get_source_limitations()["source_limitations"] == []


def test_generated_package_runtime_loads_manifest_limitations_and_relationships():
    runtime = LegalTextRuntime.from_dataset(NormalizedDataset.load(GENERATED_PACKAGE, require_search_index=True))

    coverage = runtime.get_corpus_coverage()
    assert coverage["generated_package_present"] is True
    assert coverage["package"]["schema_version"] == "generated-package.v1"
    assert coverage["manifest"]["validation_mode"] == "terminal"
    assert coverage["counts"] == {
        "laws": 1,
        "norms": 2,
        "source_limitations": 1,
        "relationships": 1,
    }

    limitations = runtime.get_source_limitations(source_family="state-law", terminal_state="source_unavailable")
    assert limitations["count"] == 1
    assert limitations["source_limitations"][0]["limitation_id"] == "lim-state-be-missing"

    relationships = runtime.get_related_norms("DSGVO", "art:5")
    assert relationships["count"] == 1
    relationship = relationships["relationships"][0]
    assert relationship["relationship_id"] == "rel-dsgvo-art5-limitation"
    assert relationship["target"]["kind"] == "source_limitation"
    assert relationship["target"]["id"] == "lim-state-be-missing"
    assert "metadata" not in relationship
    assert "text" not in json.dumps(relationship)


def test_state_law_coverage_is_optional_and_loaded_when_present(tmp_path):
    package = tmp_path / "package"
    package.mkdir()
    for name in ("laws.json", "norms.json"):
        (package / name).write_text((GENERATED_PACKAGE / name).read_text(encoding="utf-8"), encoding="utf-8")
    coverage = {
        "schema_version": "state-law-coverage.v1",
        "entries": [{"state_code": "bb", "terminal_state": "imported", "law_id": "state:bb/example"}],
        "counts": {"total_states": 1, "imported": 1, "limited": 0},
    }
    (package / "state-law-coverage.json").write_text(json.dumps(coverage), encoding="utf-8")

    dataset = NormalizedDataset.load(package)
    assert dataset.get_corpus_coverage()["state_law_coverage"] == coverage
