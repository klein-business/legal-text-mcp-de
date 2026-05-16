# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from legal_texts.state_law_inventory import FIXED_STATE_CODES
from scripts import verify_release
from scripts.benchmark_corpus_runtime import run_benchmark, write_json as write_benchmark_json
from scripts.verify_full_corpus_bundle import build_bundle, write_json as write_bundle_json


ROOT = Path(__file__).resolve().parents[2]
GENERATED_PACKAGE = ROOT / "mcp" / "tests" / "fixtures" / "generated_package"
PRIVACY_SCOPE_SEED = ROOT / "mcp" / "legal_texts" / "data" / "privacy_scope_seed.v1.json"


def write_json(path: Path, payload: object) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def package_hash(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(path.glob("*.json")):
        digest.update(item.name.encode("utf-8"))
        digest.update(item.read_bytes())
    return digest.hexdigest()


def source(source_path: str) -> dict:
    return {
        "source_kind": "gesetze-im-internet",
        "source_identifier": source_path,
        "source_url": f"https://www.gesetze-im-internet.de/{source_path}/xml.zip",
        "retrieved_at": "2026-05-15T00:00:00Z",
        "stand_date": None,
        "stand_date_status": "not_exposed",
        "content_hash": f"sha256:{source_path}",
        "source_metadata": {"source_path": source_path},
    }


def write_gii_runtime_package(package: Path) -> None:
    laws = [
        {
            "canonical_id": "bdsg_2018",
            "display_code": "BDSG",
            "display_name": "Bundesdatenschutzgesetz",
            "source": source("bdsg_2018"),
            "aliases": ["BDSG", "bdsg_2018"],
            "norm_count": 1,
            "stand_date": None,
        },
        {
            "canonical_id": "tdddg",
            "display_code": "TDDDG",
            "display_name": "Telekommunikation-Digitale-Dienste-Datenschutz-Gesetz",
            "source": source("ttdsg"),
            "aliases": ["TDDDG", "TTDSG", "ttdsg"],
            "norm_count": 1,
            "stand_date": None,
        },
    ]
    norms = [
        {
            "canonical_id": "bdsg_2018/par:1",
            "law_id": "bdsg_2018",
            "norm_id": "par:1",
            "unit": "par",
            "value": "1",
            "title": "BDSG Test",
            "text": "(1) BDSG Inhalt.",
            "status": "active",
            "url": "https://www.gesetze-im-internet.de/bdsg_2018/__1.html",
            "source": source("bdsg_2018"),
        },
        {
            "canonical_id": "tdddg/par:25",
            "law_id": "tdddg",
            "norm_id": "par:25",
            "unit": "par",
            "value": "25",
            "title": "TDDDG Test",
            "text": "(1) TDDDG Inhalt.",
            "status": "active",
            "url": "https://www.gesetze-im-internet.de/ttdsg/__25.html",
            "source": source("ttdsg"),
        },
    ]
    package.mkdir(parents=True)
    write_json(package / "laws.json", laws)
    write_json(package / "norms.json", norms)
    write_json(package / "search-index.json", {"documents": []})


def critical_outcome(source_path: str, canonical_id: str, norm_id: str) -> dict:
    return {
        "law": {"canonical_id": canonical_id, "source": source(source_path)},
        "norms": [{"canonical_id": f"{canonical_id}/{norm_id}", "norm_id": norm_id, "source": source(source_path)}],
        "limitation": None,
        "manifest_record": {
            "terminal_state": "imported",
            "source_family": "gii",
            "source_id": f"gii:{source_path}",
            "source_path": source_path,
            "source_url": f"https://www.gesetze-im-internet.de/{source_path}/xml.zip",
            "generated_law_ids": [canonical_id],
            "generated_norm_ids": [f"{canonical_id}/{norm_id}"],
        },
        "terminal_state": "imported",
    }


def gii_artifact(tmp_path: Path) -> Path:
    package = tmp_path / "gii-package"
    write_gii_runtime_package(package)
    return write_json(
        tmp_path / "gii.json",
        {
            "schema_version": "gii-corpus-gate.v1",
            "status": "ready",
            "generated_at": "2026-05-15T00:00:00Z",
            "counts": {
                "discovered_sources": 3,
                "imported_sources": 2,
                "source_unavailable": 1,
                "laws": 2,
                "norms": 2,
                "source_limitations": 1,
            },
            "terminal_state_coverage": {"imported": 2, "source_unavailable": 1},
            "generated_package": {"path": str(package), "sha256": package_hash(package)},
            "critical_law_outcomes": {
                "bdsg_2018": critical_outcome("bdsg_2018", "bdsg_2018", "par:1"),
                "tdddg": critical_outcome("ttdsg", "tdddg", "par:25"),
            },
            "validation_errors": [],
        },
    )


def dsgvo_artifact(tmp_path: Path) -> Path:
    return write_json(
        tmp_path / "dsgvo.json",
        {
            "schema_version": "dsgvo-full-counts.v1",
            "status": "ready",
            "generated_at": "2026-05-15T00:00:00Z",
            "policy": {
                "celex": "32016R0679",
                "cellar_work": "3e485e15-11bd-11e6-ba9a-01aa75ed71a1",
                "expression": "0004.02",
                "language": "de",
                "document": "DOC_2",
                "version_policy": "official-eurlex-cellar-doc2-german-expression",
                "consolidation_policy": "fixture-represents-selected-official-expression",
                "content_hash": "fixture-content-hash",
            },
            "selected_source": {
                "celex": "32016R0679",
                "cellar_work": "3e485e15-11bd-11e6-ba9a-01aa75ed71a1",
                "expression": "0004.02",
                "language": "de",
                "document": "DOC_2",
                "version_policy": "official-eurlex-cellar-doc2-german-expression",
                "consolidation_policy": "fixture-represents-selected-official-expression",
                "content_hash": "fixture-content-hash",
            },
            "expected_counts": {"articles": 99, "recitals": 173},
            "actual_counts": {"articles": 99, "recitals": 173},
            "counts": {"articles": 99, "recitals": 173},
            "boundary_samples": {
                "articles": {"expected": ["art:1", "art:99"], "found": ["art:1", "art:99"], "missing": []},
                "recitals": {"expected": ["recital:1", "recital:173"], "found": ["recital:1", "recital:173"], "missing": []},
            },
            "validation_errors": [],
        },
    )


def eu_artifact(tmp_path: Path) -> Path:
    return write_json(
        tmp_path / "eu.json",
        {
            "schema_version": "eu-neighbor-sources.v1",
            "status": "ready",
            "generated_at": "2026-05-15T00:00:00Z",
            "seeded_celex": ["32023R2854", "32024R1689"],
            "counts": {"seeded_sources": 2, "imported": 1, "limited": 1},
            "source_results": [
                {
                    "celex": "32024R1689",
                    "canonical_id": "ai_act_eu_2024_1689",
                    "terminal_state": "imported",
                    "source_url": "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32024R1689",
                    "version_policy": "official-german-eurlex-expression",
                    "generated_norm_ids": ["ai_act_eu_2024_1689/art:1"],
                },
                {
                    "celex": "32023R2854",
                    "canonical_id": "data_act_eu_2023_2854",
                    "terminal_state": "source_unavailable",
                    "source_url": "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32023R2854",
                    "version_policy": "official-german-eurlex-expression",
                    "limitation_id": "lim-data-act",
                    "limitation": {"terminal_state": "source_unavailable", "source_url": "https://eur-lex.europa.eu/legal-content/DE/TXT/?uri=CELEX:32023R2854"},
                },
            ],
            "validation_errors": [],
        },
    )


def state_artifact(tmp_path: Path) -> Path:
    package = tmp_path / "state-package"
    package.mkdir()
    states = [
        {"state_code": state_code, "terminal_state": "imported", "law_id": f"state:{state_code.lower()}/law"}
        for state_code in FIXED_STATE_CODES
    ]
    coverage = {
        "schema_version": "state-law-coverage.v1",
        "counts": {"total_states": 16, "imported": 16, "limited": 0, "pdf_source_count": 0, "pdf_extraction_count": 0},
        "states": states,
    }
    coverage_path = write_json(package / "state-law-coverage.json", coverage)
    return write_json(
        tmp_path / "state.json",
        {
            "schema_version": "state-law-pdf-source-gate.v1",
            "status": "ready",
            "generated_at": "2026-05-15T00:00:00Z",
            "counts": coverage["counts"],
            "coverage_path": str(coverage_path),
            "coverage_sha256": hashlib.sha256(coverage_path.read_bytes()).hexdigest(),
            "validation_errors": [],
        },
    )


def artifact_set(tmp_path: Path) -> dict[str, Path]:
    benchmark, _ = run_benchmark(GENERATED_PACKAGE, queries=["personenbezogene"])
    benchmark_path = tmp_path / "benchmark.json"
    write_benchmark_json(benchmark_path, benchmark)
    return {
        "gii_artifact": gii_artifact(tmp_path),
        "dsgvo_artifact": dsgvo_artifact(tmp_path),
        "eu_neighbors_artifact": eu_artifact(tmp_path),
        "state_law_artifact": state_artifact(tmp_path),
        "relationships_artifact": PRIVACY_SCOPE_SEED,
        "benchmark_artifact": benchmark_path,
    }


def test_benchmark_outputs_runtime_decision_fields(tmp_path):
    benchmark, exit_code = run_benchmark(GENERATED_PACKAGE, queries=["personenbezogene", "schutz"])

    assert exit_code == 0
    assert benchmark["schema_version"] == "corpus-runtime-benchmark.v1"
    assert benchmark["status"] == "passed"
    assert benchmark["thresholds"] == {"max_load_ms": 120000.0, "max_search_p95_ms": 1000.0, "max_memory_mb": 2048.0}
    assert benchmark["record_counts"]["laws"] == 1
    assert benchmark["record_counts"]["norms"] == 2
    assert "p95_ms" in benchmark["sampled_search"]
    assert "python_version" in benchmark["environment"]
    assert benchmark["dataset_memory_bytes"] > 0
    assert benchmark["search_memory_bytes"] > 0
    assert benchmark["combined_memory_bytes"] >= benchmark["dataset_memory_bytes"] + benchmark["search_memory_bytes"]
    assert "migration_decisions" in benchmark

    output = tmp_path / "benchmark.json"
    write_benchmark_json(output, benchmark)
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == "corpus-runtime-benchmark.v1"


def test_benchmark_threshold_misses_are_acceptable_with_migration_decisions():
    benchmark, exit_code = run_benchmark(
        GENERATED_PACKAGE,
        queries=["personenbezogene"],
        thresholds={"max_load_ms": 0.0, "max_search_p95_ms": 0.0, "max_memory_mb": 0.0},
    )

    assert exit_code == 0
    assert benchmark["status"] == "passed_with_migration_decisions"
    decisions = {item["decision"] for item in benchmark["migration_decisions"]}
    assert "review_dataset_loading_strategy" in decisions
    assert "consider_external_or_persisted_search_index" in decisions
    assert "consider_memory_mapped_or_chunked_runtime_loading" in decisions


def test_full_corpus_bundle_success_with_contract_artifacts(tmp_path):
    bundle, exit_code = build_bundle(**artifact_set(tmp_path))

    assert exit_code == 0
    assert bundle["schema_version"] == "full-corpus-validation-bundle.v1"
    for section in ("gii", "dsgvo", "critical_laws", "eu_neighbors", "state_law", "relationships", "runtime_readiness", "benchmark"):
        assert section in bundle
    for section in ("gii", "dsgvo", "eu_neighbors", "state_law", "relationships", "benchmark"):
        assert bundle[section]["source_artifact"] == bundle[section]["path"]
        assert bundle[section]["generated_at"]
        assert bundle[section]["errors"] == []
    assert bundle["runtime_readiness"]["status"] == "ready"
    assert bundle["critical_laws"]["status"] == "ready"
    assert bundle["critical_laws"]["evidence"]["bdsg_2018"]["resolution"]["runtime"]["status"] == "resolved"
    assert bundle["critical_laws"]["evidence"]["tdddg"]["outcome_key"] == "tdddg"
    assert bundle["validation_errors"] == []

    output = tmp_path / "bundle.json"
    write_bundle_json(output, bundle)
    assert json.loads(output.read_text(encoding="utf-8"))["schema_version"] == "full-corpus-validation-bundle.v1"


def test_full_corpus_bundle_reports_missing_artifacts(tmp_path):
    artifacts = artifact_set(tmp_path)
    artifacts["gii_artifact"] = tmp_path / "missing-gii.json"

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert bundle["gii"]["status"] == "missing"
    assert any("gii: artifact missing" in error for error in bundle["validation_errors"])
    assert any("critical_laws" in error for error in bundle["validation_errors"])


def test_placeholder_section_artifacts_fail(tmp_path):
    benchmark, _ = run_benchmark(GENERATED_PACKAGE, queries=["personenbezogene"])
    benchmark_path = tmp_path / "benchmark.json"
    write_benchmark_json(benchmark_path, benchmark)

    def placeholder(name: str, schema: str) -> Path:
        return write_json(
            tmp_path / name,
            {
                "schema_version": schema,
                "status": "ready",
                "generated_at": "2026-05-15T00:00:00Z",
                "validation_errors": [],
            },
        )

    bundle, exit_code = build_bundle(
        gii_artifact=placeholder("gii.json", "gii-corpus-gate.v1"),
        dsgvo_artifact=placeholder("dsgvo.json", "dsgvo-full-counts.v1"),
        eu_neighbors_artifact=placeholder("eu.json", "eu-neighbor-sources.v1"),
        state_law_artifact=placeholder("state.json", "state-law-pdf-source-gate.v1"),
        relationships_artifact=placeholder("relationships.json", "privacy-scope-seed.v1"),
        benchmark_artifact=benchmark_path,
    )

    assert exit_code == 1
    assert any("gii: missing terminal_state_coverage" in error for error in bundle["validation_errors"])
    assert any("dsgvo: missing policy content_hash" in error for error in bundle["validation_errors"])
    assert any("eu_neighbors: source_results must cover seeded_celex" in error for error in bundle["validation_errors"])
    assert any("state_law: total_states must be 16" in error for error in bundle["validation_errors"])
    assert any("relationships: relationship_source must be an object" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_missing_gii_terminal_coverage(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw.pop("terminal_state_coverage")
    artifacts["gii_artifact"] = write_json(tmp_path / "bad-gii.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("gii: missing terminal_state_coverage" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_missing_dsgvo_content_hash(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["dsgvo_artifact"].read_text(encoding="utf-8"))
    raw["policy"].pop("content_hash")
    artifacts["dsgvo_artifact"] = write_json(tmp_path / "bad-dsgvo.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("dsgvo: missing policy content_hash" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_missing_eu_source_results(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["eu_neighbors_artifact"].read_text(encoding="utf-8"))
    raw["source_results"] = []
    artifacts["eu_neighbors_artifact"] = write_json(tmp_path / "bad-eu.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("eu_neighbors: source_results must cover seeded_celex" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_wrong_state_total(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["state_law_artifact"].read_text(encoding="utf-8"))
    raw["counts"]["total_states"] = 15
    artifacts["state_law_artifact"] = write_json(tmp_path / "bad-state.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("state_law: total_states must be 16" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_unknown_state_codes(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["state_law_artifact"].read_text(encoding="utf-8"))
    coverage_path = Path(raw["coverage_path"])
    coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    coverage["states"][0]["state_code"] = "XX"
    bad_coverage_path = write_json(tmp_path / "bad-state-coverage.json", coverage)
    raw["coverage_path"] = str(bad_coverage_path)
    artifacts["state_law_artifact"] = write_json(tmp_path / "bad-state.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("state_law: missing coverage states" in error for error in bundle["validation_errors"])
    assert any("state_law: unknown coverage states ['XX']" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_invalid_relationship_seed(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(PRIVACY_SCOPE_SEED.read_text(encoding="utf-8"))
    raw["relationships"] = []
    raw["source_limitations"] = []
    artifacts["relationships_artifact"] = write_json(tmp_path / "bad-relationships.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("relationships: relationships or source_limitations must be nonempty" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_weak_critical_law_evidence(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw["critical_law_outcomes"]["bdsg_2018"]["manifest_record"].pop("generated_norm_ids")
    artifacts["gii_artifact"] = write_json(tmp_path / "bad-critical.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("critical_laws: bdsg_2018 imported evidence missing generated_norm_ids" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_cross_wired_critical_law_evidence(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw["critical_law_outcomes"]["bdsg_2018"]["manifest_record"]["generated_law_ids"] = ["tdddg"]
    raw["critical_law_outcomes"]["bdsg_2018"]["manifest_record"]["generated_norm_ids"] = ["tdddg/par:25"]
    artifacts["gii_artifact"] = write_json(tmp_path / "cross-wired-critical.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("critical_laws: bdsg_2018 generated_law_ids must include bdsg_2018" in error for error in bundle["validation_errors"])
    assert any("critical_laws: bdsg_2018 generated_norm_ids must all belong to bdsg_2018" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_weak_release_blocking_limitation(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw["critical_law_outcomes"]["bdsg_2018"] = {
        "terminal_state": "parse_failed",
        "manifest_record": {"terminal_state": "parse_failed", "source_id": "gii:bdsg_2018", "source_path": "bdsg_2018"},
        "limitation": {"terminal_state": "parse_failed", "source_url": "https://www.gesetze-im-internet.de/bdsg_2018/xml.zip", "release_blocking": True},
    }
    artifacts["gii_artifact"] = write_json(tmp_path / "bad-limitation.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("critical_laws: bdsg_2018 limitation must use terminal_state source_unavailable" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_under_specified_source_unavailable_limitation(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw["critical_law_outcomes"]["bdsg_2018"] = {
        "terminal_state": "source_unavailable",
        "manifest_record": {"terminal_state": "source_unavailable", "source_id": "gii:bdsg_2018", "source_path": "bdsg_2018"},
        "limitation": {
            "terminal_state": "source_unavailable",
            "source_id": "gii:bdsg_2018",
            "source_path": "bdsg_2018",
            "source_url": "https://www.gesetze-im-internet.de/bdsg_2018/xml.zip",
            "release_blocking": True,
        },
    }
    artifacts["gii_artifact"] = write_json(tmp_path / "weak-source-unavailable.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("critical_laws: bdsg_2018 limitation missing limitation_id" in error for error in bundle["validation_errors"])
    assert any("critical_laws: bdsg_2018 limitation missing substantive upstream evidence details" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_source_path_only_upstream_evidence(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw["critical_law_outcomes"]["bdsg_2018"] = {
        "terminal_state": "source_unavailable",
        "manifest_record": {"terminal_state": "source_unavailable", "source_id": "gii:bdsg_2018", "source_path": "bdsg_2018"},
        "limitation": {
            "limitation_id": "lim-bdsg-unavailable",
            "terminal_state": "source_unavailable",
            "source_id": "gii:bdsg_2018",
            "source_path": "bdsg_2018",
            "source_url": "https://www.gesetze-im-internet.de/bdsg_2018/xml.zip",
            "reason": "official source unavailable",
            "retrieved_at": "2026-05-15T00:00:00Z",
            "details": {"source_path": "bdsg_2018", "release_blocking": True},
        },
    }
    artifacts["gii_artifact"] = write_json(tmp_path / "source-path-only-limitation.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("critical_laws: bdsg_2018 limitation missing substantive upstream evidence details" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_empty_upstream_evidence_values(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw["critical_law_outcomes"]["bdsg_2018"] = {
        "terminal_state": "source_unavailable",
        "manifest_record": {"terminal_state": "source_unavailable", "source_id": "gii:bdsg_2018", "source_path": "bdsg_2018"},
        "limitation": {
            "limitation_id": "lim-bdsg-unavailable",
            "terminal_state": "source_unavailable",
            "source_id": "gii:bdsg_2018",
            "source_path": "bdsg_2018",
            "source_url": "https://www.gesetze-im-internet.de/bdsg_2018/xml.zip",
            "reason": "official source unavailable",
            "retrieved_at": "2026-05-15T00:00:00Z",
            "details": {"source_path": "bdsg_2018", "content_type": "", "error_code": "", "http_status": 0, "release_blocking": True},
        },
    }
    artifacts["gii_artifact"] = write_json(tmp_path / "empty-upstream-evidence.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("critical_laws: bdsg_2018 limitation missing substantive upstream evidence details" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_rejects_boolean_http_status_evidence(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw["critical_law_outcomes"]["bdsg_2018"] = {
        "terminal_state": "source_unavailable",
        "manifest_record": {"terminal_state": "source_unavailable", "source_id": "gii:bdsg_2018", "source_path": "bdsg_2018"},
        "limitation": {
            "limitation_id": "lim-bdsg-unavailable",
            "terminal_state": "source_unavailable",
            "source_id": "gii:bdsg_2018",
            "source_path": "bdsg_2018",
            "source_url": "https://www.gesetze-im-internet.de/bdsg_2018/xml.zip",
            "reason": "official source unavailable",
            "retrieved_at": "2026-05-15T00:00:00Z",
            "details": {"source_path": "bdsg_2018", "http_status": True, "release_blocking": True},
        },
    }
    artifacts["gii_artifact"] = write_json(tmp_path / "boolean-http-status-evidence.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 1
    assert any("critical_laws: bdsg_2018 limitation missing substantive upstream evidence details" in error for error in bundle["validation_errors"])


def test_full_corpus_bundle_accepts_legacy_ttdsg_critical_key(tmp_path):
    artifacts = artifact_set(tmp_path)
    raw = json.loads(artifacts["gii_artifact"].read_text(encoding="utf-8"))
    raw["critical_law_outcomes"]["ttdsg"] = raw["critical_law_outcomes"].pop("tdddg")
    artifacts["gii_artifact"] = write_json(tmp_path / "legacy-gii.json", raw)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 0
    assert bundle["critical_laws"]["evidence"]["tdddg"]["outcome_key"] == "ttdsg"


def test_bundle_accepts_threshold_misses_with_complete_migration_decisions(tmp_path):
    artifacts = artifact_set(tmp_path)
    benchmark, exit_code = run_benchmark(
        GENERATED_PACKAGE,
        queries=["personenbezogene"],
        thresholds={"max_load_ms": 0.0, "max_search_p95_ms": 0.0, "max_memory_mb": 0.0},
    )
    assert exit_code == 0
    artifacts["benchmark_artifact"] = write_json(tmp_path / "missed-benchmark.json", benchmark)

    bundle, exit_code = build_bundle(**artifacts)

    assert exit_code == 0
    assert bundle["runtime_readiness"]["status"] == "ready"
    assert bundle["runtime_readiness"]["benchmark_status"] == "passed_with_migration_decisions"
    assert {item["decision"] for item in bundle["migration_decisions"]} == {
        "review_dataset_loading_strategy",
        "consider_external_or_persisted_search_index",
        "consider_memory_mapped_or_chunked_runtime_loading",
    }


def test_gitignore_and_release_gate_hygiene():
    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert ".artifacts/" in gitignore
    for ignored in ("data/sources/raw/", "data/normalized/", "data/generated/", "data/full-corpus/"):
        assert ignored in gitignore
    assert not any(line.strip() == "mcp/tests/fixtures/" for line in gitignore.splitlines())

    release_gate = (ROOT / "scripts" / "verify_release.py").read_text(encoding="utf-8")
    assert "test_operational_corpus_gates.py" in release_gate
    assert "test_search_scaling.py" in release_gate
    assert "test_source_matrix_live.py" not in verify_release.selected_tests()
    assert "mcp/tests/test_source_matrix_live.py" not in verify_release.selected_tests()
    assert "benchmark_corpus_runtime.py" not in release_gate
    assert "verify_full_corpus_bundle.py" not in release_gate


def test_release_gate_live_source_matrix_is_explicit_opt_in(monkeypatch):
    monkeypatch.delenv("RUN_LIVE_SOURCE_MATRIX", raising=False)
    assert "mcp/tests/test_source_matrix_live.py" not in verify_release.selected_tests()

    monkeypatch.setenv("RUN_LIVE_SOURCE_MATRIX", "true")
    assert "mcp/tests/test_source_matrix_live.py" in verify_release.selected_tests()
