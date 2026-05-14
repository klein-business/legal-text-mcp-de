import json
from pathlib import Path


ROOT = Path(__file__).parent
DATASET = ROOT / "fixtures" / "normalized"
EXPECTED = ROOT / "fixtures" / "fixture_inventory_expected.json"


def test_fixture_inventory_expected_matches_normalized_records():
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    norms = json.loads((DATASET / "norms.json").read_text(encoding="utf-8"))
    available = {norm["canonical_id"] for norm in norms}
    missing = [
        f"{law_id}/{norm_id}"
        for law_id, norm_ids in expected.items()
        for norm_id in norm_ids
        if f"{law_id}/{norm_id}" not in available
    ]
    assert not missing


def test_fixture_inventory_markdown_mentions_all_required_laws():
    text = Path("plans/reliable-law-data-mcp/fixture-inventory.md").read_text(encoding="utf-8")
    expected = json.loads(EXPECTED.read_text(encoding="utf-8"))
    for law_id in expected:
        assert f"`{law_id}`" in text
