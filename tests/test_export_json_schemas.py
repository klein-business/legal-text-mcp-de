# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import json

from scripts import export_json_schemas


def test_export_is_deterministic_and_contains_response_contracts(tmp_path):
    export_json_schemas.export_schemas(tmp_path)
    first = {p.name: p.read_bytes() for p in tmp_path.glob("*.schema.json")}
    assert "LawListResponse.schema.json" in first
    health = json.loads(first["HealthResponse.schema.json"])
    assert health["required"] == ["status"]
    assert health["properties"]["status"]["type"] == "string"
    assert "BaseModel.schema.json" not in first
    export_json_schemas.export_schemas(tmp_path)
    assert {p.name: p.read_bytes() for p in tmp_path.glob("*.schema.json")} == first


def test_export_removes_stale_generated_schemas(tmp_path):
    (tmp_path / "RemovedResponse.schema.json").write_text("{}")
    (tmp_path / "index.md").write_text("Keep this documentation")
    export_json_schemas.export_schemas(tmp_path)
    assert not (tmp_path / "RemovedResponse.schema.json").exists()
    assert (tmp_path / "index.md").read_text() == "Keep this documentation"
