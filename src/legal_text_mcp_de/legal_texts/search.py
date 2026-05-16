# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path
from typing import Any

from .dataset import NormalizedDataset
from .errors import invalid_query


TOKEN_RE = re.compile(r"\w+", re.UNICODE)
DEFAULT_SNIPPET_CHARS = 240
DEFAULT_LIMIT = 20


def normalize_query(query: str) -> tuple[str, list[str]]:
    normalized = unicodedata.normalize("NFKC", query).casefold().strip()
    normalized = " ".join(normalized.split())
    tokens = []
    seen = set()
    for token in TOKEN_RE.findall(normalized):
        if token not in seen:
            tokens.append(token)
            seen.add(token)
    if not normalized or not tokens:
        raise invalid_query("Search query is empty after normalization.", {"query": query})
    return normalized, tokens


def tokenize(text: str) -> list[str]:
    return TOKEN_RE.findall(unicodedata.normalize("NFKC", text).casefold())


class SearchService:
    def __init__(
        self, dataset: NormalizedDataset, *, limit: int = DEFAULT_LIMIT, snippet_chars: int = DEFAULT_SNIPPET_CHARS
    ) -> None:
        self.dataset = dataset
        self.limit = limit
        self.snippet_chars = snippet_chars
        self.rows = [self._row(norm) for norm in dataset.iter_text_norms()]

    def write_index_marker(self) -> None:
        marker = self.dataset.path / "search-index.json"
        marker.write_text(json.dumps({"state": "ready", "count": len(self.rows)}, indent=2), encoding="utf-8")

    def search_laws(self, query: str, codes: list[str] | None = None) -> dict[str, Any]:
        normalized_query, terms = normalize_query(query)
        filter_ids = None
        if codes:
            filter_ids = sorted({self.dataset.registry.resolve_law(code)["canonical_id"] for code in codes})
        hits = []
        for row in self.rows:
            if filter_ids and row["law_id"] not in filter_ids:
                continue
            counts = {term: row["tokens"].count(term) for term in terms}
            if any(count == 0 for count in counts.values()):
                continue
            raw_score = sum(counts.values())
            hits.append((raw_score, row))
        if not hits:
            return {"query": normalized_query, "codes": filter_ids, "results": [], "count": 0}
        top = max(score for score, _ in hits)
        results = []
        for raw_score, row in hits:
            score = 1.0 if raw_score == top else round(raw_score / top, 6)
            result = {
                "law_id": row["law_id"],
                "law_display_code": row["law_display_code"],
                "law_display_name": row["law_display_name"],
                "norm_id": row["norm_id"],
                "canonical_id": row["canonical_id"],
                "title": row["title"],
                "snippet": self._snippet(row["indexed_text"], terms),
                "source": row["source"],
                "url": row["url"],
                "score": score,
            }
            results.append(result)
        results.sort(key=lambda item: (-item["score"], item["law_id"], item["norm_id"]))
        results = results[: self.limit]
        return {"query": normalized_query, "codes": filter_ids, "results": results, "count": len(results)}

    def _row(self, norm: dict[str, Any]) -> dict[str, Any]:
        law = self.dataset.laws_by_id[norm["law_id"]]
        indexed_text = " ".join(part for part in [norm.get("title") or "", norm.get("text") or ""] if part)
        return {
            "law_id": norm["law_id"],
            "law_display_code": law["display_code"],
            "law_display_name": law["display_name"],
            "norm_id": norm["norm_id"],
            "canonical_id": norm["canonical_id"],
            "title": norm.get("title"),
            "indexed_text": indexed_text,
            "tokens": tokenize(indexed_text),
            "source": norm["source"],
            "url": norm["url"],
        }

    def _snippet(self, text: str, terms: list[str]) -> str:
        collapsed = " ".join(text.split())
        lowered = unicodedata.normalize("NFKC", collapsed).casefold()
        positions = [lowered.find(term) for term in terms if lowered.find(term) >= 0]
        start = min(positions) if positions else 0
        half = self.snippet_chars // 2
        window_start = max(0, start - half)
        window_end = min(len(collapsed), window_start + self.snippet_chars)
        snippet = collapsed[window_start:window_end]
        if window_start > 0:
            snippet = "..." + snippet[3:]
        if window_end < len(collapsed):
            snippet = snippet[:-3] + "..."
        return snippet


def ensure_search_index(dataset_path: Path, dataset: NormalizedDataset) -> None:
    SearchService(dataset).write_index_marker()
