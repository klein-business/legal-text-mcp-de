from __future__ import annotations

import json
from pathlib import Path

from .eurlex_xml import parse_dsgvo_xml
from .gii_xml import parse_gii_zip
from .registry import LawRegistry


def normalize_snapshot(manifest_path: Path, output_dir: Path, registry: LawRegistry | None = None) -> dict:
    registry = registry or LawRegistry.load()
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_dir.mkdir(parents=True, exist_ok=True)
    laws = []
    norms = []
    for entry in manifest.get("entries", []):
        law_entry = registry.resolve_law(entry["canonical_id"])
        raw_path = Path(entry["raw_path"])
        source = entry["source"]
        law_norms = (
            parse_dsgvo_xml(raw_path, law_entry, source)
            if law_entry["source_kind"] == "eur-lex-cellar"
            else parse_gii_zip(raw_path, law_entry, source)
        )
        laws.append(
            {
                "canonical_id": law_entry["canonical_id"],
                "display_code": law_entry["display_code"],
                "display_name": law_entry["display_name"],
                "source": source,
                "aliases": law_entry.get("aliases", []),
                "norm_count": len(law_norms),
                "stand_date": source.get("stand_date"),
            }
        )
        norms.extend(law_norms)
    (output_dir / "laws.json").write_text(json.dumps(laws, ensure_ascii=False, indent=2), encoding="utf-8")
    (output_dir / "norms.json").write_text(json.dumps(norms, ensure_ascii=False, indent=2), encoding="utf-8")
    readiness = {"stage": "normalized_dataset", "state": "ready", "details": {"law_count": len(laws), "norm_count": len(norms)}}
    (output_dir / "readiness.json").write_text(json.dumps(readiness, ensure_ascii=False, indent=2), encoding="utf-8")
    return readiness
