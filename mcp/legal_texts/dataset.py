from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .errors import dataset_not_ready, law_not_found, norm_not_found
from .models import norm_summary
from .registry import LawRegistry
from .validation import validate_dataset_package, validate_laws, validate_norms


class NormalizedDataset:
    def __init__(self, path: Path, registry: LawRegistry | None = None, *, require_search_index: bool = False) -> None:
        self.path = Path(path)
        self.registry = registry or LawRegistry.load()
        stage = "serving_dataset" if require_search_index else "normalized_dataset"
        readiness = validate_dataset_package(self.path, stage=stage)
        if readiness.state != "ready":
            raise dataset_not_ready("Dataset is not ready.", readiness.to_dict())
        self.readiness = readiness
        self.laws = json.loads((self.path / "laws.json").read_text(encoding="utf-8"))
        self.norms = json.loads((self.path / "norms.json").read_text(encoding="utf-8"))
        validation_errors = validate_laws(self.laws) + validate_norms(self.norms)
        if validation_errors:
            raise dataset_not_ready("Dataset validation failed.", {"errors": validation_errors, "path": str(self.path)})
        self.laws_by_id = {law["canonical_id"]: law for law in self.laws}
        self.norms_by_canonical = {norm["canonical_id"]: norm for norm in self.norms}
        self.norms_by_law: dict[str, list[dict[str, Any]]] = {}
        for norm in self.norms:
            self.norms_by_law.setdefault(norm["law_id"], []).append(norm)

    @classmethod
    def load(cls, path: str | Path, registry: LawRegistry | None = None, *, require_search_index: bool = False) -> "NormalizedDataset":
        return cls(Path(path), registry, require_search_index=require_search_index)

    def list_laws(self, query: str | None = None) -> dict[str, Any]:
        laws = sorted(self.laws, key=lambda law: law["canonical_id"])
        if query:
            needle = query.casefold()
            laws = [
                law
                for law in laws
                if needle in law["canonical_id"].casefold()
                or needle in law["display_code"].casefold()
                or needle in law["display_name"].casefold()
                or any(needle in alias.casefold() for alias in law.get("aliases", []))
            ]
        return {"laws": laws, "count": len(laws), "query": query}

    def get_law(self, code: str) -> dict[str, Any]:
        entry = self.registry.resolve_law(code)
        law_id = entry["canonical_id"]
        law = self.laws_by_id.get(law_id)
        if not law:
            raise law_not_found(code)
        norms = [norm_summary(norm) for norm in sorted(self.norms_by_law.get(law_id, []), key=lambda item: item["norm_id"])]
        return {"law": law, "norms": norms}

    def law_record(self, code: str) -> dict[str, Any]:
        entry = self.registry.resolve_law(code)
        law = self.laws_by_id.get(entry["canonical_id"])
        if not law:
            raise law_not_found(code)
        return law

    def get_norm_by_id(self, law_id: str, norm_id: str) -> dict[str, Any]:
        canonical = f"{law_id}/{norm_id}"
        norm = self.norms_by_canonical.get(canonical)
        if not norm:
            suggestions = [
                norm_summary(item)
                for item in self.norms_by_law.get(law_id, [])
                if item["norm_id"].split(":", 1)[0] == norm_id.split(":", 1)[0]
            ][:10]
            raise norm_not_found(law_id, norm_id, suggestions=suggestions)
        return norm

    def get_source_metadata(self, code: str | None = None) -> dict[str, Any]:
        laws = [self.law_record(code)] if code else sorted(self.laws, key=lambda law: law["canonical_id"])
        sources = [
            {
                "law_id": law["canonical_id"],
                "display_code": law["display_code"],
                "display_name": law["display_name"],
                "source": law["source"],
            }
            for law in laws
        ]
        return {"sources": sources, "count": len(sources)}

    def iter_text_norms(self) -> list[dict[str, Any]]:
        return [norm for norm in self.norms if norm.get("text")]
