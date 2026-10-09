# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Export the public HTTP models as deterministic JSON Schema files."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel

from legal_text_mcp_de import http_models  # type: ignore[import-untyped]


def export_schemas(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    names: set[str] = set()
    for name, model in sorted(vars(http_models).items()):
        if (
            name.startswith("_")
            or not isinstance(model, type)
            or not issubclass(model, BaseModel)
            or model.__module__ != http_models.__name__
        ):
            continue
        filename = f"{name}.schema.json"
        names.add(filename)
        (output_dir / filename).write_text(
            json.dumps(model.model_json_schema(), indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
    for stale in output_dir.glob("*.schema.json"):
        if stale.name not in names:
            stale.unlink()
    print(f"Exported {len(names)} JSON Schemas to {output_dir}")


if __name__ == "__main__":
    export_schemas(Path(__file__).resolve().parents[1] / "docs" / "schemas")
