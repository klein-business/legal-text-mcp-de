# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .dataset import NormalizedDataset
from .errors import LegalTextError, dataset_not_ready
from .registry import LawRegistry
from .resolver import get_norm, resolve_citation
from .search import SearchService


@dataclass
class LegalTextRuntime:
    dataset_path: Path | None
    registry: LawRegistry
    dataset: NormalizedDataset | None
    search: SearchService | None
    startup_error: LegalTextError | None = None

    @classmethod
    def from_settings(cls, settings: Any, *, strict: bool | None = None) -> "LegalTextRuntime":
        registry = LawRegistry.load()
        strict_startup = settings.strict_startup if strict is None else strict
        if not settings.dataset_path:
            error = dataset_not_ready("DATASET_PATH is not configured.", {"stage": "serving_dataset", "state": "missing"})
            if strict_startup:
                raise error
            return cls(None, registry, None, None, startup_error=error)
        try:
            dataset = NormalizedDataset.load(settings.dataset_path, registry, require_search_index=True)
            search = SearchService(dataset)
            return cls(Path(settings.dataset_path), registry, dataset, search)
        except LegalTextError as exc:
            if strict_startup:
                raise
            return cls(Path(settings.dataset_path), registry, None, None, startup_error=exc)

    @classmethod
    def from_dataset(cls, dataset: NormalizedDataset) -> "LegalTextRuntime":
        return cls(dataset.path, dataset.registry, dataset, SearchService(dataset))

    def readiness(self) -> dict[str, Any]:
        if self.startup_error:
            raise self.startup_error
        if not self.dataset:
            raise dataset_not_ready("Dataset is not loaded.", {"stage": "serving_dataset", "state": "missing"})
        return {"stage": "serving_dataset", "state": "ready", "details": {"path": str(self.dataset.path)}}

    def require_dataset(self) -> NormalizedDataset:
        if self.startup_error:
            raise self.startup_error
        if not self.dataset:
            raise dataset_not_ready("Dataset is not loaded.", {"stage": "serving_dataset", "state": "missing"})
        return self.dataset

    def list_laws(self, query: str | None = None) -> dict[str, Any]:
        return self.require_dataset().list_laws(query)

    def get_law(self, code: str) -> dict[str, Any]:
        return self.require_dataset().get_law(code)

    def get_source_metadata(self, code: str | None = None) -> dict[str, Any]:
        return self.require_dataset().get_source_metadata(code)

    def get_corpus_coverage(self) -> dict[str, Any]:
        return self.require_dataset().get_corpus_coverage()

    def get_source_limitations(
        self,
        source_family: str | None = None,
        terminal_state: str | None = None,
        state_code: str | None = None,
        law_id: str | None = None,
    ) -> dict[str, Any]:
        return self.require_dataset().get_source_limitations(
            source_family=source_family,
            terminal_state=terminal_state,
            state_code=state_code,
            law_id=law_id,
        )

    def get_related_norms(self, code: str, norm: str) -> dict[str, Any]:
        citation = get_norm(self.require_dataset(), code, norm)
        return self.require_dataset().get_related_norms(
            citation["law"]["canonical_id"],
            citation["norm"]["norm_id"],
        )

    def get_norm(self, code: str, norm: str) -> dict[str, Any]:
        return get_norm(self.require_dataset(), code, norm)

    def resolve_citation(self, **kwargs: Any) -> dict[str, Any]:
        return resolve_citation(self.require_dataset(), **kwargs)

    def search_laws(self, query: str, codes: list[str] | None = None) -> dict[str, Any]:
        if self.startup_error:
            raise self.startup_error
        if not self.search:
            raise dataset_not_ready("Search index is not loaded.", {"stage": "serving_dataset", "state": "missing"})
        return self.search.search_laws(query, codes)
