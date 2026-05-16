# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
import unicodedata
from pathlib import Path
from typing import Any

from .errors import ambiguous_law_alias, law_not_found


DEFAULT_REGISTRY_PATH = Path(__file__).with_name("data") / "laws.v1.json"


def normalize_alias(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value).casefold().strip()
    return " ".join(normalized.split())


class LawRegistry:
    def __init__(self, entries: list[dict[str, Any]], *, validate: bool = True) -> None:
        self.entries = entries
        self.by_id = {entry["canonical_id"]: entry for entry in entries}
        self.alias_index: dict[str, list[dict[str, Any]]] = {}
        for entry in entries:
            values = set(entry.get("aliases", [])) | {entry["canonical_id"], entry["display_code"]}
            for alias in values:
                self.alias_index.setdefault(normalize_alias(alias), []).append(entry)
        if validate:
            self.validate()

    @classmethod
    def from_entries(cls, entries: list[dict[str, Any]], *, validate: bool = True) -> "LawRegistry":
        return cls(entries, validate=validate)

    @classmethod
    def load(cls, path: Path | None = None) -> "LawRegistry":
        registry_path = path or DEFAULT_REGISTRY_PATH
        data = json.loads(registry_path.read_text(encoding="utf-8"))
        return cls(data["laws"], validate=True)

    def validate(self) -> None:
        if len(self.by_id) != len(self.entries):
            raise ValueError("Duplicate canonical law IDs in registry")
        collisions = {
            alias: entries
            for alias, entries in self.alias_index.items()
            if len({entry["canonical_id"] for entry in entries}) > 1
        }
        if collisions:
            details = ", ".join(sorted(collisions))
            raise ValueError(f"Alias collisions in registry: {details}")

    def all_laws(self) -> list[dict[str, Any]]:
        return sorted(self.entries, key=lambda entry: entry["canonical_id"])

    def resolve_law(self, code: str) -> dict[str, Any]:
        normalized = normalize_alias(code)
        matches = self.alias_index.get(normalized, [])
        unique = {entry["canonical_id"]: entry for entry in matches}
        if not unique:
            raise law_not_found(code, suggestions=self.suggest(code))
        if len(unique) > 1:
            raise ambiguous_law_alias(code, list(unique.values()))
        return next(iter(unique.values()))

    def suggest(self, code: str, *, limit: int = 10) -> list[dict[str, Any]]:
        needle = normalize_alias(code)
        scored: list[tuple[int, dict[str, Any]]] = []
        for entry in self.entries:
            aliases = [entry["canonical_id"], entry["display_code"], *entry.get("aliases", [])]
            score = max(_simple_similarity(needle, normalize_alias(alias)) for alias in aliases)
            scored.append((score, entry))
        scored.sort(key=lambda item: (-item[0], item[1]["canonical_id"]))
        return [
            {
                "canonical_id": entry["canonical_id"],
                "display_code": entry["display_code"],
                "display_name": entry["display_name"],
            }
            for _, entry in scored[:limit]
        ]


def _simple_similarity(a: str, b: str) -> int:
    if not a or not b:
        return 0
    if a == b:
        return 100
    if a in b or b in a:
        return 80
    common = len(set(a.split()) & set(b.split()))
    return common * 20
