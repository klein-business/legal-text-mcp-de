# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
from pathlib import Path

from legal_text_mcp_de.legal_texts.dataset import NormalizedDataset
from legal_text_mcp_de.legal_texts.search import SearchService
from scripts.benchmark_corpus_runtime import run_benchmark


ROOT = Path(__file__).resolve().parents[1]
GENERATED_PACKAGE = ROOT / "tests" / "fixtures" / "generated_package"


def build_scaled_legacy_package(tmp_path: Path, *, norm_count: int = 160) -> Path:
    package = tmp_path / "scaled-package"
    package.mkdir()
    laws = json.loads((GENERATED_PACKAGE / "laws.json").read_text(encoding="utf-8"))
    base_norm = json.loads((GENERATED_PACKAGE / "norms.json").read_text(encoding="utf-8"))[0]
    norms = []
    for index in range(1, norm_count + 1):
        norm = dict(base_norm)
        norm["canonical_id"] = f"dsgvo_eu_2016_679/art:{index}"
        norm["norm_id"] = f"art:{index}"
        norm["value"] = str(index)
        norm["title"] = f"Artikel {index}"
        norm["text"] = f"Skalierter Datenschutz Testtext Nummer {index}. Personenbezogene Daten und Suchbegriff {index % 7}."
        norms.append(norm)
    laws[0]["norm_count"] = len(norms)
    (package / "laws.json").write_text(json.dumps(laws), encoding="utf-8")
    (package / "norms.json").write_text(json.dumps(norms), encoding="utf-8")
    (package / "search-index.json").write_text(json.dumps({"state": "ready", "count": len(norms)}), encoding="utf-8")
    return package


def test_search_handles_larger_fixture_backed_package(tmp_path):
    package = build_scaled_legacy_package(tmp_path)
    dataset = NormalizedDataset.load(package, require_search_index=True)
    search = SearchService(dataset, limit=25)

    result = search.search_laws("personenbezogene daten")

    assert result["count"] == 25
    assert result["results"][0]["law_id"] == "dsgvo_eu_2016_679"
    assert all("personenbezogene" in item["snippet"].casefold() for item in result["results"][:5])


def test_benchmark_handles_scaled_fixture_package(tmp_path):
    package = build_scaled_legacy_package(tmp_path, norm_count=120)

    benchmark, exit_code = run_benchmark(package, queries=["personenbezogene daten", "suchbegriff 3"])

    assert exit_code == 0
    assert benchmark["record_counts"]["norms"] == 120
    assert benchmark["sampled_search"]["p95_ms"] >= 0
    assert benchmark["package_size_bytes"] > 0
    assert benchmark["dataset_memory_bytes"] > 0
    assert benchmark["search_memory_bytes"] > 0
    assert benchmark["combined_memory_bytes"] >= benchmark["dataset_memory_bytes"] + benchmark["search_memory_bytes"]
    assert benchmark["estimated_memory_bytes"] == benchmark["combined_memory_bytes"]
    assert benchmark["validation_errors"] == []
