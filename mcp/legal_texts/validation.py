from __future__ import annotations

from pathlib import Path
from typing import Any

from .models import Readiness


REQUIRED_LAW_FIELDS = {"canonical_id", "display_code", "display_name", "source", "aliases", "norm_count"}
REQUIRED_NORM_FIELDS = {"canonical_id", "law_id", "norm_id", "unit", "value", "status", "url", "source"}
REQUIRED_SOURCE_FIELDS = {
    "source_kind",
    "source_identifier",
    "source_url",
    "retrieved_at",
    "stand_date_status",
    "content_hash",
}


def validate_dataset_package(path: Path, *, stage: str = "normalized_dataset") -> Readiness:
    if not path.exists():
        return Readiness(stage=stage, state="missing", details={"path": str(path)})
    laws_file = path / "laws.json"
    norms_file = path / "norms.json"
    if not laws_file.exists() or not norms_file.exists():
        return Readiness(
            stage=stage,
            state="invalid",
            details={"missing_files": [name for name in ("laws.json", "norms.json") if not (path / name).exists()]},
        )
    if stage == "serving_dataset" and not (path / "search-index.json").exists():
        return Readiness(
            stage=stage,
            state="invalid",
            details={"search_index_status": "pending"},
        )
    return Readiness(stage=stage, state="ready", details={"path": str(path)})


def validate_laws(laws: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for law in laws:
        missing = REQUIRED_LAW_FIELDS - set(law)
        if missing:
            errors.append(f"{law.get('canonical_id', '<unknown>')}: missing law fields {sorted(missing)}")
        law_id = law.get("canonical_id")
        if law_id in seen:
            errors.append(f"{law_id}: duplicate law ID")
        seen.add(law_id)
        errors.extend(_validate_source(law.get("source", {}), law_id or "<unknown>"))
    return errors


def validate_norms(norms: list[dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for norm in norms:
        missing = REQUIRED_NORM_FIELDS - set(norm)
        if missing:
            errors.append(f"{norm.get('canonical_id', '<unknown>')}: missing norm fields {sorted(missing)}")
        canonical_id = norm.get("canonical_id")
        if canonical_id in seen:
            errors.append(f"{canonical_id}: duplicate norm ID")
        seen.add(canonical_id)
        if norm.get("status") not in {"container"} and not norm.get("text"):
            errors.append(f"{canonical_id}: active norm requires text")
        if not str(norm.get("url", "")).startswith("https://"):
            errors.append(f"{canonical_id}: URL must be HTTPS")
        errors.extend(_validate_source(norm.get("source", {}), canonical_id or "<unknown>"))
    return errors


def _validate_source(source: dict[str, Any], owner: str) -> list[str]:
    missing = REQUIRED_SOURCE_FIELDS - set(source)
    if missing:
        return [f"{owner}: missing source fields {sorted(missing)}"]
    if source.get("source_kind") == "eur-lex-cellar":
        metadata = source.get("source_metadata") or {}
        required = {"celex", "cellar_work", "expression", "language", "document"}
        missing_meta = required - set(metadata)
        if missing_meta:
            return [f"{owner}: missing EUR-Lex metadata {sorted(missing_meta)}"]
    if source.get("source_kind") == "gesetze-im-internet":
        metadata = source.get("source_metadata") or {}
        if "source_path" not in metadata:
            return [f"{owner}: missing GII source_path"]
    return []
