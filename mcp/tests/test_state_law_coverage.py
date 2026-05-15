from __future__ import annotations

from pathlib import Path

from legal_texts.state_law import run_state_law_adapters
from legal_texts.state_law_coverage import (
    build_state_law_coverage,
    validate_state_law_coverage,
)
from legal_texts.state_law_inventory import (
    DEFAULT_STATE_LAW_INVENTORY_PATH,
    DEFAULT_STATE_LAW_LIMITATIONS_PATH,
    FIXED_STATE_CODES,
    load_state_law_inventory,
    load_state_law_limitations,
)


FIXTURE_DIR = Path(__file__).parent / "fixtures" / "state_law"


def build_phase9_fixture(tmp_path: Path) -> tuple[dict, Path]:
    inventory = load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH)
    limitations = load_state_law_limitations(DEFAULT_STATE_LAW_LIMITATIONS_PATH)
    bb = (FIXTURE_DIR / "official_like_bb.html").read_bytes()
    nw = (FIXTURE_DIR / "official_like_nw.html").read_bytes()
    malformed = (FIXTURE_DIR / "malformed_html_law.html").read_bytes()
    by_url = {
        next(record for record in inventory["states"] if record["state_code"] == "BB")["official_sources"][0]["url"]: bb,
        next(record for record in inventory["states"] if record["state_code"] == "NW")["official_sources"][0]["url"]: nw,
    }

    def fake_fetch(url: str) -> tuple[int, dict[str, str], bytes]:
        return 200, {"content-type": "text/html; charset=utf-8"}, by_url.get(url, malformed)

    result = run_state_law_adapters(
        inventory,
        limitations,
        package_dir=tmp_path / "package",
        retrieved_at="2026-05-15T00:00:00Z",
        fetch=fake_fetch,
    )
    artifact = {
        "schema_version": "state-law-adapter-gate.v1",
        "generated_at": "2026-05-15T00:00:00Z",
        "counts": {
            "imported": result.terminal_state_counts.get("imported", 0),
            "source_limitations": len(result.source_limitations),
        },
        "source_outcomes": result.source_outcomes,
        "validation_errors": result.validation_errors,
    }
    return artifact, tmp_path / "package"


def assert_has_error(errors: list[str], expected: str) -> None:
    assert any(expected in error for error in errors), errors


def test_state_law_coverage_contains_exact_fixed_state_set(tmp_path):
    inventory = load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH)
    phase9, package_dir = build_phase9_fixture(tmp_path)

    coverage = build_state_law_coverage(inventory, phase9, package_dir=package_dir)

    assert coverage["schema_version"] == "state-law-coverage.v1"
    assert coverage["counts"] == {
        "total_states": 16,
        "imported": 2,
        "limited": 14,
        "pdf_source_count": 0,
        "pdf_extraction_count": 0,
    }
    assert {entry["state_code"] for entry in coverage["states"]} == set(FIXED_STATE_CODES)
    assert validate_state_law_coverage(coverage, inventory, phase9, package_dir=package_dir) == []


def test_state_law_coverage_resolves_imports_and_phase8_limitations(tmp_path):
    inventory = load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH)
    phase9, package_dir = build_phase9_fixture(tmp_path)

    coverage = build_state_law_coverage(inventory, phase9, package_dir=package_dir)
    by_state = {entry["state_code"]: entry for entry in coverage["states"]}

    assert by_state["BB"]["terminal_state"] == "imported"
    assert by_state["BB"]["law_id"] == "state:bb/brandenburgisches-datenschutzgesetz"
    assert by_state["NW"]["terminal_state"] == "imported"
    assert by_state["HB"]["source_limitation_id"] == "lim-state-hb-dsg-source-limitation"
    assert by_state["NI"]["source_limitation_id"] == "lim-state-ni-dsg-source-limitation"
    assert by_state["SL"]["source_limitation_id"] == "lim-state-sl-dsg-source-limitation"


def test_state_law_coverage_rejects_missing_duplicate_and_dangling_entries(tmp_path):
    inventory = load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH)
    phase9, package_dir = build_phase9_fixture(tmp_path)
    coverage = build_state_law_coverage(inventory, phase9, package_dir=package_dir)
    missing = dict(coverage)
    missing["states"] = [entry for entry in coverage["states"] if entry["state_code"] != "BW"]
    duplicate = dict(coverage)
    duplicate["states"] = [*coverage["states"], dict(coverage["states"][0])]
    dangling_law = dict(coverage)
    dangling_law["states"] = [dict(entry) for entry in coverage["states"]]
    next(entry for entry in dangling_law["states"] if entry["state_code"] == "BB")["law_id"] = "state:bb/missing"
    dangling_limitation = dict(coverage)
    dangling_limitation["states"] = [dict(entry) for entry in coverage["states"]]
    next(entry for entry in dangling_limitation["states"] if entry["state_code"] == "HB")["source_limitation_id"] = "missing-lim"

    assert_has_error(validate_state_law_coverage(missing, inventory, phase9, package_dir=package_dir), "missing coverage states ['BW']")
    assert_has_error(validate_state_law_coverage(duplicate, inventory, phase9, package_dir=package_dir), "duplicate coverage state BB")
    assert_has_error(validate_state_law_coverage(dangling_law, inventory, phase9, package_dir=package_dir), "law_id state:bb/missing not found")
    assert_has_error(validate_state_law_coverage(dangling_limitation, inventory, phase9, package_dir=package_dir), "source_limitation_id missing-lim not found")


def test_state_law_coverage_rejects_wrong_existing_limitation_binding(tmp_path):
    inventory = load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH)
    phase9, package_dir = build_phase9_fixture(tmp_path)
    coverage = build_state_law_coverage(inventory, phase9, package_dir=package_dir)
    swapped = dict(coverage)
    swapped["states"] = [dict(entry) for entry in coverage["states"]]
    hb = next(entry for entry in swapped["states"] if entry["state_code"] == "HB")
    hb["source_limitation_id"] = "lim-state-ni-dsg-source-limitation"

    errors = validate_state_law_coverage(swapped, inventory, phase9, package_dir=package_dir)

    assert_has_error(errors, "HB: source_limitation_id lim-state-ni-dsg-source-limitation source_id state-law:ni/niedersaechsisches-datenschutzgesetz does not match coverage source_id state-law:hb/bremisches-datenschutzgesetz")
    assert_has_error(errors, "HB: source_limitation_id lim-state-ni-dsg-source-limitation state_code ni does not match coverage state_code HB")


def test_state_law_coverage_rejects_limitation_terminal_state_mismatch(tmp_path):
    inventory = load_state_law_inventory(DEFAULT_STATE_LAW_INVENTORY_PATH)
    phase9, package_dir = build_phase9_fixture(tmp_path)
    coverage = build_state_law_coverage(inventory, phase9, package_dir=package_dir)
    mismatched = dict(coverage)
    mismatched["states"] = [dict(entry) for entry in coverage["states"]]
    hb = next(entry for entry in mismatched["states"] if entry["state_code"] == "HB")
    hb["terminal_state"] = "parse_failed"

    errors = validate_state_law_coverage(mismatched, inventory, phase9, package_dir=package_dir)

    assert_has_error(errors, "HB: source_limitation_id lim-state-hb-dsg-source-limitation terminal_state source_unavailable does not match coverage terminal_state parse_failed")
