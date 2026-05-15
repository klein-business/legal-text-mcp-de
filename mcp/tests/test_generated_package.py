from __future__ import annotations

import hashlib
import json
import shutil
from pathlib import Path
from typing import Any

from legal_texts.dataset import NormalizedDataset
from legal_texts.validation import validate_dataset_package, validate_generated_package


FIXTURES = Path(__file__).parent / "fixtures"
LEGACY_PACKAGE = FIXTURES / "normalized"
GENERATED_PACKAGE = FIXTURES / "generated_package"


def copy_generated_package(tmp_path: Path) -> Path:
    target = tmp_path / "package"
    shutil.copytree(GENERATED_PACKAGE, target)
    return target


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_package_hash(package_path: Path, relative_path: str) -> None:
    package = load_json(package_path / "package.json")
    digest = hashlib.sha256((package_path / relative_path).read_bytes()).hexdigest()
    package["content_hashes"][relative_path] = f"sha256:{digest}"
    write_json(package_path / "package.json", package)


def update_package_count(package_path: Path, key: str, value: int) -> None:
    package = load_json(package_path / "package.json")
    package["record_counts"][key] = value
    write_json(package_path / "package.json", package)


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def test_legacy_package_without_package_json_keeps_existing_readiness_and_loading():
    readiness = validate_dataset_package(LEGACY_PACKAGE, stage="serving_dataset")

    assert readiness.state == "ready"
    assert NormalizedDataset.load(LEGACY_PACKAGE, require_search_index=True).laws


def test_valid_generated_package_passes_strict_validation_and_loads():
    assert validate_generated_package(GENERATED_PACKAGE, require_search_index=True) == []

    readiness = validate_dataset_package(GENERATED_PACKAGE, stage="serving_dataset")

    assert readiness.state == "ready"
    assert NormalizedDataset.load(GENERATED_PACKAGE, require_search_index=True).laws


def test_generated_package_reports_package_metadata_errors(tmp_path):
    package_path = copy_generated_package(tmp_path)
    package = load_json(package_path / "package.json")
    package.pop("dataset_id")
    package["schema_version"] = "wrong"
    package["generator"].pop("version")
    write_json(package_path / "package.json", package)

    readiness = validate_dataset_package(package_path)

    assert readiness.state == "invalid"
    assert readiness.details["path"] == str(package_path)
    assert_has_error(readiness.details["errors"], "package.json missing fields ['dataset_id']")
    assert_has_error(readiness.details["errors"], "package.json schema_version must be generated-package.v1")
    assert_has_error(readiness.details["errors"], "package.json generator missing fields ['version']")


def test_generated_package_rejects_directory_package_json_without_raising(tmp_path):
    package_path = copy_generated_package(tmp_path)
    (package_path / "package.json").unlink()
    (package_path / "package.json").mkdir()

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "package.json must be a file")


def test_generated_package_rejects_manifest_record_mismatch(tmp_path):
    package_path = copy_generated_package(tmp_path)
    manifest = load_json(package_path / "manifest.json")
    manifest["discovered_sources"][0]["generated_norm_ids"].append("dsgvo_eu_2016_679/art:999")
    write_json(package_path / "manifest.json", manifest)
    update_package_hash(package_path, "manifest.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "manifest imported generated_norm_id dsgvo_eu_2016_679/art:999 not found in norms.json")


def test_generated_package_rejects_extra_law_not_declared_by_imported_manifest_source(tmp_path):
    package_path = copy_generated_package(tmp_path)
    laws = load_json(package_path / "laws.json")
    extra_law = dict(laws[0])
    extra_law["canonical_id"] = "extra_privacy_law"
    extra_law["display_code"] = "EXTRA"
    extra_law["norm_count"] = 0
    laws.append(extra_law)
    write_json(package_path / "laws.json", laws)
    update_package_hash(package_path, "laws.json")
    update_package_count(package_path, "laws", len(laws))

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "laws.json contains extra law extra_privacy_law not declared by imported manifest sources")


def test_generated_package_rejects_extra_norm_not_declared_by_imported_manifest_source(tmp_path):
    package_path = copy_generated_package(tmp_path)
    laws = load_json(package_path / "laws.json")
    norms = load_json(package_path / "norms.json")
    extra_norm = dict(norms[0])
    extra_norm["canonical_id"] = "dsgvo_eu_2016_679/art:999"
    extra_norm["norm_id"] = "art:999"
    extra_norm["value"] = "999"
    norms.append(extra_norm)
    laws[0]["norm_count"] = len(norms)
    write_json(package_path / "laws.json", laws)
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "laws.json")
    update_package_hash(package_path, "norms.json")
    update_package_count(package_path, "norms", len(norms))

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "norms.json contains extra norm dsgvo_eu_2016_679/art:999 not declared by imported manifest sources")


def test_generated_package_rejects_directory_laws_json_without_raising(tmp_path):
    package_path = copy_generated_package(tmp_path)
    (package_path / "laws.json").unlink()
    (package_path / "laws.json").mkdir()

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "laws.json must be a file")


def test_generated_package_rejects_directory_norms_json_without_raising(tmp_path):
    package_path = copy_generated_package(tmp_path)
    (package_path / "norms.json").unlink()
    (package_path / "norms.json").mkdir()

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "norms.json must be a file")


def test_generated_package_rejects_package_source_limitation_not_declared_by_manifest(tmp_path):
    package_path = copy_generated_package(tmp_path)
    limitations = load_json(package_path / "source-limitations.json")
    extra_limitation = dict(limitations[0])
    extra_limitation["limitation_id"] = "lim-extra"
    extra_limitation["source_id"] = "state-law:be/extra"
    limitations.append(extra_limitation)
    write_json(package_path / "source-limitations.json", limitations)
    update_package_hash(package_path, "source-limitations.json")
    update_package_count(package_path, "source_limitations", len(limitations))

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "lim-extra: source limitation is not declared by manifest source_limitations")


def test_generated_package_rejects_source_limitation_same_id_contradiction(tmp_path):
    package_path = copy_generated_package(tmp_path)
    limitations = load_json(package_path / "source-limitations.json")
    limitations[0]["source_family"] = "gii"
    limitations[0]["source_id"] = "gii:contradiction"
    limitations[0]["terminal_state"] = "parse_failed"
    limitations[0]["source_url"] = "https://example.test/contradiction"
    limitations[0]["retrieved_at"] = "2026-05-16T00:00:00Z"
    write_json(package_path / "source-limitations.json", limitations)
    update_package_hash(package_path, "source-limitations.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "lim-state-be-missing: source limitation source_family gii does not match manifest source_family state-law")
    assert_has_error(errors, "lim-state-be-missing: source limitation source_id gii:contradiction does not match manifest source_id state-law:be/missing")
    assert_has_error(errors, "lim-state-be-missing: source limitation terminal_state parse_failed does not match manifest terminal_state source_unavailable")
    assert_has_error(errors, "lim-state-be-missing: source limitation source_url https://example.test/contradiction does not match manifest source_url https://example.test/be/missing")
    assert_has_error(errors, "lim-state-be-missing: source limitation retrieved_at 2026-05-16T00:00:00Z does not match manifest retrieved_at 2026-05-15T00:00:00Z")


def test_generated_package_rejects_imported_source_limitation_terminal_state(tmp_path):
    package_path = copy_generated_package(tmp_path)
    limitations = load_json(package_path / "source-limitations.json")
    limitations[0]["terminal_state"] = "imported"
    write_json(package_path / "source-limitations.json", limitations)
    update_package_hash(package_path, "source-limitations.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "lim-state-be-missing: source limitation terminal_state must not be imported")


def test_generated_package_rejects_relationship_source_not_declared_by_manifest(tmp_path):
    package_path = copy_generated_package(tmp_path)
    relationships = load_json(package_path / "relationships.json")
    relationships[0]["source_id"] = "third-party-scope:unknown"
    write_json(package_path / "relationships.json", relationships)
    update_package_hash(package_path, "relationships.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "rel-dsgvo-art5-limitation: relationship source ('third-party-scope', 'third-party-scope:unknown') is not declared by manifest relationship_sources")


def test_generated_package_rejects_unresolved_relationship_target(tmp_path):
    package_path = copy_generated_package(tmp_path)
    relationships = load_json(package_path / "relationships.json")
    relationships[0]["object"]["id"] = "missing-limitation"
    write_json(package_path / "relationships.json", relationships)
    update_package_hash(package_path, "relationships.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "rel-dsgvo-art5-limitation: object target source_limitation:missing-limitation does not resolve")


def test_generated_package_rejects_external_source_relationship_target(tmp_path):
    package_path = copy_generated_package(tmp_path)
    relationships = load_json(package_path / "relationships.json")
    relationships[0]["object"] = {"kind": "external_source", "id": "https://example.test/outside"}
    write_json(package_path / "relationships.json", relationships)
    update_package_hash(package_path, "relationships.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "rel-dsgvo-art5-limitation: object target kind external_source is not supported")


def test_generated_package_rejects_relationship_missing_provenance(tmp_path):
    package_path = copy_generated_package(tmp_path)
    relationships = load_json(package_path / "relationships.json")
    relationships[0].pop("provenance")
    write_json(package_path / "relationships.json", relationships)
    update_package_hash(package_path, "relationships.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "rel-dsgvo-art5-limitation: missing relationship fields ['provenance']")


def test_generated_package_rejects_duplicate_relationship_ids(tmp_path):
    package_path = copy_generated_package(tmp_path)
    relationships = load_json(package_path / "relationships.json")
    relationships.append(dict(relationships[0]))
    write_json(package_path / "relationships.json", relationships)
    update_package_hash(package_path, "relationships.json")
    update_package_count(package_path, "relationships", len(relationships))

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "duplicate relationship_id rel-dsgvo-art5-limitation")


def test_generated_package_rejects_unsupported_relationship_type(tmp_path):
    package_path = copy_generated_package(tmp_path)
    relationships = load_json(package_path / "relationships.json")
    relationships[0]["relationship_type"] = "summarizes"
    write_json(package_path / "relationships.json", relationships)
    update_package_hash(package_path, "relationships.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "rel-dsgvo-art5-limitation: unsupported relationship_type summarizes")


def test_generated_package_rejects_nested_relationship_copied_text_fields(tmp_path):
    package_path = copy_generated_package(tmp_path)
    relationships = load_json(package_path / "relationships.json")
    relationships[0]["metadata"]["nested"] = {"editorial_text": "copied text is forbidden"}
    write_json(package_path / "relationships.json", relationships)
    update_package_hash(package_path, "relationships.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "rel-dsgvo-art5-limitation: relationship must not include copied/editorial text fields ['metadata.nested.editorial_text']")


def test_generated_package_rejects_directory_relationships_json_without_raising(tmp_path):
    package_path = copy_generated_package(tmp_path)
    (package_path / "relationships.json").unlink()
    (package_path / "relationships.json").mkdir()

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "relationships.json must be a file")


def test_generated_package_rejects_count_mismatch(tmp_path):
    package_path = copy_generated_package(tmp_path)
    package = load_json(package_path / "package.json")
    package["record_counts"]["laws"] = 2
    write_json(package_path / "package.json", package)

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "record_counts.laws=2 does not match actual count 1")


def test_generated_package_rejects_content_hash_mismatch(tmp_path):
    package_path = copy_generated_package(tmp_path)
    laws = load_json(package_path / "laws.json")
    laws[0]["display_name"] = "Changed"
    write_json(package_path / "laws.json", laws)

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "content_hashes.laws.json does not match file contents")


def test_generated_package_rejects_package_json_in_content_hashes(tmp_path):
    package_path = copy_generated_package(tmp_path)
    package = load_json(package_path / "package.json")
    package["content_hashes"]["package.json"] = "sha256:self"
    write_json(package_path / "package.json", package)

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "content_hashes must not include package.json")


def test_generated_package_rejects_empty_content_hashes(tmp_path):
    package_path = copy_generated_package(tmp_path)
    package = load_json(package_path / "package.json")
    package["content_hashes"] = {}
    write_json(package_path / "package.json", package)

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "content_hashes missing required package file laws.json")
    assert_has_error(errors, "content_hashes missing required package file norms.json")
    assert_has_error(errors, "content_hashes missing required package file manifest.json")
    assert_has_error(errors, "content_hashes missing required package file readiness.json")


def test_generated_package_rejects_present_optional_file_missing_from_content_hashes(tmp_path):
    package_path = copy_generated_package(tmp_path)
    package = load_json(package_path / "package.json")
    package["content_hashes"].pop("search-index.json")
    write_json(package_path / "package.json", package)

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "content_hashes missing present optional package file search-index.json")


def test_generated_package_rejects_directory_content_hash_target_without_raising(tmp_path):
    package_path = copy_generated_package(tmp_path)
    package = load_json(package_path / "package.json")
    package["content_hashes"]["."] = "sha256:directory"
    write_json(package_path / "package.json", package)

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "content_hashes.. must reference a file")


def test_generated_package_rejects_directory_source_limitations_json_without_raising(tmp_path):
    package_path = copy_generated_package(tmp_path)
    (package_path / "source-limitations.json").unlink()
    (package_path / "source-limitations.json").mkdir()

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "source-limitations.json must be a file")


def test_generated_package_rejects_missing_declared_readiness_path(tmp_path):
    package_path = copy_generated_package(tmp_path)
    (package_path / "readiness.json").unlink()

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "readiness.json is missing")


def test_generated_package_rejects_directory_manifest_path_without_raising(tmp_path):
    package_path = copy_generated_package(tmp_path)
    package = load_json(package_path / "package.json")
    package["manifest_path"] = "."
    package["content_hashes"].pop("manifest.json")
    package["content_hashes"]["."] = "sha256:directory"
    write_json(package_path / "package.json", package)

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "manifest.json must be a file")


def test_generated_package_rejects_directory_readiness_path_without_raising(tmp_path):
    package_path = copy_generated_package(tmp_path)
    package = load_json(package_path / "package.json")
    package["readiness_path"] = "."
    package["content_hashes"].pop("readiness.json")
    package["content_hashes"]["."] = "sha256:directory"
    write_json(package_path / "package.json", package)

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "readiness.json must be a file")


def test_generated_package_accepts_additive_generated_units(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    values = {
        "par": "1",
        "art": "2",
        "recital": "3",
        "chapter": "fixture",
        "section": "scope-1",
        "annex": "a_1",
        "container": "recitals",
    }
    for unit in ("par", "art", "recital", "chapter", "section", "annex", "container"):
        value = values[unit]
        norm = dict(norms[0])
        norm["canonical_id"] = f"dsgvo_eu_2016_679/{unit}:{value}"
        norm["norm_id"] = f"{unit}:{value}"
        norm["unit"] = unit
        norm["value"] = value
        norm["status"] = "container" if unit == "container" else "active"
        norm["text"] = None if unit == "container" else f"{unit} text"
        norms.append(norm)
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")
    laws = load_json(package_path / "laws.json")
    laws[0]["norm_count"] = len(norms)
    write_json(package_path / "laws.json", laws)
    update_package_hash(package_path, "laws.json")
    package = load_json(package_path / "package.json")
    package["record_counts"]["norms"] = len(norms)
    write_json(package_path / "package.json", package)
    manifest = load_json(package_path / "manifest.json")
    manifest["discovered_sources"][0]["generated_norm_ids"] = [norm["canonical_id"] for norm in norms]
    write_json(package_path / "manifest.json", manifest)
    update_package_hash(package_path, "manifest.json")

    errors = validate_generated_package(package_path)

    assert errors == []


def test_generated_package_rejects_malformed_structural_norm_value(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["unit"] = "container"
    norms[1]["value"] = "recitals?"
    norms[1]["norm_id"] = "container:recitals?"
    norms[1]["canonical_id"] = "dsgvo_eu_2016_679/container:recitals?"
    norms[1]["status"] = "container"
    norms[1].pop("text", None)
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/container:recitals?: container value must match")


def test_generated_package_rejects_malformed_numeric_norm_value(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["unit"] = "recital"
    norms[1]["value"] = "intro"
    norms[1]["norm_id"] = "recital:intro"
    norms[1]["canonical_id"] = "dsgvo_eu_2016_679/recital:intro"
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/recital:intro: recital value must match")


def test_generated_package_rejects_norm_id_value_mismatch(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["unit"] = "container"
    norms[1]["value"] = "recitals"
    norms[1]["norm_id"] = "container:other"
    norms[1]["canonical_id"] = "dsgvo_eu_2016_679/container:other"
    norms[1]["status"] = "container"
    norms[1].pop("text", None)
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/container:other: norm_id must equal container:recitals")


def test_generated_package_rejects_non_lowercase_structural_norm_values(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["unit"] = "container"
    norms[1]["value"] = "Recitals"
    norms[1]["norm_id"] = "container:Recitals"
    norms[1]["canonical_id"] = "dsgvo_eu_2016_679/container:Recitals"
    norms[1]["status"] = "container"
    norms[1].pop("text", None)
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/container:Recitals: value must be canonical lowercase")
    assert_has_error(errors, "dsgvo_eu_2016_679/container:Recitals: norm_id must be canonical lowercase")
    assert_has_error(errors, "dsgvo_eu_2016_679/container:Recitals: canonical_id must be canonical lowercase")


def test_generated_package_rejects_non_lowercase_chapter_value(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["unit"] = "chapter"
    norms[1]["value"] = "Overview"
    norms[1]["norm_id"] = "chapter:Overview"
    norms[1]["canonical_id"] = "dsgvo_eu_2016_679/chapter:Overview"
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/chapter:Overview: value must be canonical lowercase")
    assert_has_error(errors, "dsgvo_eu_2016_679/chapter:Overview: chapter value must match")


def test_generated_package_rejects_non_lowercase_numeric_suffix(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[0]["value"] = "5A"
    norms[0]["norm_id"] = "art:5A"
    norms[0]["canonical_id"] = "dsgvo_eu_2016_679/art:5A"
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/art:5A: value must be canonical lowercase")
    assert_has_error(errors, "dsgvo_eu_2016_679/art:5A: art value must match")


def test_generated_package_rejects_uppercase_canonical_id_even_with_lowercase_norm_id(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["canonical_id"] = "DSGVO_EU_2016_679/recital:1"
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "DSGVO_EU_2016_679/recital:1: canonical_id must be canonical lowercase")


def test_generated_package_rejects_invalid_generated_unit(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["unit"] = "clause"
    norms[1]["norm_id"] = "clause:1"
    norms[1]["canonical_id"] = "dsgvo_eu_2016_679/clause:1"
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/clause:1: unsupported norm unit clause")


def test_generated_package_rejects_malformed_container_unit_status_combinations(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["unit"] = "container"
    norms[1]["norm_id"] = "container:recitals"
    norms[1]["canonical_id"] = "dsgvo_eu_2016_679/container:recitals"
    norms[1]["status"] = "active"
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/container:recitals: container unit requires container status")


def test_generated_package_rejects_container_status_on_non_container_unit(tmp_path):
    package_path = copy_generated_package(tmp_path)
    norms = load_json(package_path / "norms.json")
    norms[1]["status"] = "container"
    norms[1].pop("text")
    write_json(package_path / "norms.json", norms)
    update_package_hash(package_path, "norms.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "dsgvo_eu_2016_679/recital:1: container status requires container unit")


def test_generated_package_rejects_malformed_readiness_when_present(tmp_path):
    package_path = copy_generated_package(tmp_path)
    readiness = load_json(package_path / "readiness.json")
    readiness["state"] = "warming"
    readiness.pop("details")
    write_json(package_path / "readiness.json", readiness)
    update_package_hash(package_path, "readiness.json")

    errors = validate_generated_package(package_path)

    assert_has_error(errors, "readiness.json state must be one of")
    assert_has_error(errors, "readiness.json missing fields ['details']")
