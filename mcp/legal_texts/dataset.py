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
        self.generated_package_present = (self.path / "package.json").exists()
        self.package_metadata = self._load_json_if_present("package.json", {})
        manifest_path = self.package_metadata.get("manifest_path", "manifest.json")
        self.manifest = self._load_json_if_present(str(manifest_path), {})
        self.source_limitations = self._load_json_if_present("source-limitations.json", [])
        self.relationships = self._load_json_if_present("relationships.json", [])
        self.state_law_coverage = self._load_json_if_present("state-law-coverage.json", {})
        self.source_limitations_by_id = {
            limitation["limitation_id"]: limitation
            for limitation in self.source_limitations
            if isinstance(limitation, dict) and limitation.get("limitation_id")
        }

    @classmethod
    def load(cls, path: str | Path, registry: LawRegistry | None = None, *, require_search_index: bool = False) -> "NormalizedDataset":
        return cls(Path(path), registry, require_search_index=require_search_index)

    def _load_json_if_present(self, relative_path: str, default: Any) -> Any:
        path = self.path / relative_path
        if not path.is_file():
            return default.copy() if isinstance(default, (dict, list)) else default
        return json.loads(path.read_text(encoding="utf-8"))

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

    def get_corpus_coverage(self) -> dict[str, Any]:
        manifest_sources = self.manifest.get("discovered_sources", []) if isinstance(self.manifest, dict) else []
        terminal_states: dict[str, int] = {}
        source_families: set[str] = set()
        for source in manifest_sources:
            if not isinstance(source, dict):
                continue
            if source.get("terminal_state"):
                state = str(source["terminal_state"])
                terminal_states[state] = terminal_states.get(state, 0) + 1
            if source.get("source_family"):
                source_families.add(str(source["source_family"]))
        for law in self.laws:
            source = law.get("source", {})
            metadata = source.get("source_metadata", {}) if isinstance(source, dict) else {}
            if source.get("source_kind"):
                source_families.add(str(source["source_kind"]))
            if metadata.get("source_family"):
                source_families.add(str(metadata["source_family"]))

        return {
            "generated_package_present": self.generated_package_present,
            "package": self.package_metadata,
            "manifest": self._manifest_summary(),
            "counts": {
                "laws": len(self.laws),
                "norms": len(self.norms),
                "source_limitations": len(self.source_limitations),
                "relationships": len(self.relationships),
            },
            "source_families": sorted(source_families),
            "terminal_states": terminal_states,
            "state_law_coverage": self.state_law_coverage,
        }

    def get_source_limitations(
        self,
        *,
        source_family: str | None = None,
        terminal_state: str | None = None,
        state_code: str | None = None,
        law_id: str | None = None,
    ) -> dict[str, Any]:
        limitations = list(self.source_limitations)
        if source_family:
            limitations = [item for item in limitations if item.get("source_family") == source_family]
        if terminal_state:
            limitations = [item for item in limitations if item.get("terminal_state") == terminal_state]
        if state_code:
            needle = state_code.casefold()
            limitations = [item for item in limitations if str(item.get("state_code", "")).casefold() == needle]
        if law_id:
            limitations = [
                item
                for item in limitations
                if item.get("law_id") == law_id
                or item.get("target_law_id") == law_id
                or item.get("details", {}).get("law_id") == law_id
            ]
        return {
            "source_limitations": limitations,
            "count": len(limitations),
            "filters": {
                "source_family": source_family,
                "terminal_state": terminal_state,
                "state_code": state_code,
                "law_id": law_id,
            },
        }

    def get_related_norms(self, law_id: str, norm_id: str) -> dict[str, Any]:
        canonical = f"{law_id}/{norm_id}"
        norm = self.get_norm_by_id(law_id, norm_id)
        related: list[dict[str, Any]] = []
        for relationship in self.relationships:
            subject = relationship.get("subject", {})
            object_ = relationship.get("object", {})
            direction = None
            target = None
            if subject.get("kind") == "norm" and subject.get("id") == canonical:
                direction = "outgoing"
                target = object_
            elif object_.get("kind") == "norm" and object_.get("id") == canonical:
                direction = "incoming"
                target = subject
            if not direction or not isinstance(target, dict):
                continue
            related.append(
                {
                    "relationship_id": relationship.get("relationship_id"),
                    "relationship_type": relationship.get("relationship_type"),
                    "direction": direction,
                    "subject": subject,
                    "object": object_,
                    "source_family": relationship.get("source_family"),
                    "source_id": relationship.get("source_id"),
                    "provenance": relationship.get("provenance"),
                    "target": self._relationship_target_summary(target),
                }
            )
        return {"norm": norm_summary(norm), "relationships": related, "count": len(related)}

    def iter_text_norms(self) -> list[dict[str, Any]]:
        return [norm for norm in self.norms if norm.get("text")]

    def _manifest_summary(self) -> dict[str, Any]:
        if not isinstance(self.manifest, dict) or not self.manifest:
            return {}
        return {
            "schema_version": self.manifest.get("schema_version"),
            "dataset_id": self.manifest.get("dataset_id"),
            "package_id": self.manifest.get("package_id"),
            "validation_mode": self.manifest.get("validation_mode"),
            "created_at": self.manifest.get("created_at"),
            "discovered_sources": len(self.manifest.get("discovered_sources", [])),
            "source_limitations": len(self.manifest.get("source_limitations", [])),
            "relationship_sources": len(self.manifest.get("relationship_sources", [])),
        }

    def _relationship_target_summary(self, endpoint: dict[str, Any]) -> dict[str, Any]:
        kind = endpoint.get("kind")
        target_id = endpoint.get("id")
        if kind == "law" and target_id in self.laws_by_id:
            law = self.laws_by_id[target_id]
            return {
                "kind": "law",
                "id": target_id,
                "display_code": law.get("display_code"),
                "display_name": law.get("display_name"),
            }
        if kind == "norm" and target_id in self.norms_by_canonical:
            return {"kind": "norm", "id": target_id, "norm": norm_summary(self.norms_by_canonical[target_id])}
        if kind == "source_limitation" and target_id in self.source_limitations_by_id:
            limitation = self.source_limitations_by_id[target_id]
            return {
                "kind": "source_limitation",
                "id": target_id,
                "source_family": limitation.get("source_family"),
                "source_id": limitation.get("source_id"),
                "terminal_state": limitation.get("terminal_state"),
                "reason": limitation.get("reason"),
                "source_url": limitation.get("source_url"),
                "state_code": limitation.get("state_code"),
            }
        return {"kind": kind, "id": target_id, "resolved": False}
