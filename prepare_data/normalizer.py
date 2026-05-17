# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Bridges per-source NormalizedLaw structs into the runtime's dict schema.

The runtime's NormalizedDataset.load expects each law as a JSON-shaped dict
with specific keys. This module converts NormalizedLaw (produced by the
state-law scrapers and EU-act loaders) into that shape.
"""

from __future__ import annotations

from typing import Any

from prepare_data.state_law.base import NormalizedLaw


def normalize_for_runtime(
    laws: list[NormalizedLaw],
    *,
    source_kind: str,
    retrieved_at: str,
) -> list[dict[str, Any]]:
    """Produce the dict-list consumed by NormalizedDataset.load.

    Parameters
    ----------
    laws
        Normalised laws emitted by per-source scrapers/loaders.
    source_kind
        Marker used in the runtime's source metadata, e.g. ``"state-bayern"``,
        ``"eur-lex-cellar"``.
    retrieved_at
        ISO 8601 UTC timestamp (ending in ``Z``) for when the laws were fetched.

    Returns
    -------
    list[dict[str, Any]]
        One dict per law, ready to merge into a bundle. The ``content_hash``
        field is left empty here and filled by the bundle packager later.
    """
    out: list[dict[str, Any]] = []
    for law in laws:
        out.append(
            {
                "canonical_id": law.canonical_id,
                "display_code": law.display_code,
                "display_name": law.display_name,
                "aliases": [],
                "norm_count": len(law.norms),
                "stand_date": None,
                "source": {
                    "source_kind": source_kind,
                    "source_identifier": law.canonical_id,
                    "source_url": law.source_url,
                    "retrieved_at": retrieved_at,
                    "stand_date": None,
                    "stand_date_status": "not_exposed",
                    "content_hash": "",  # filled by packager later
                },
                "norms": [
                    {
                        "norm_id": n.norm_id,
                        "title": n.title,
                        "text": n.text,
                    }
                    for n in law.norms
                ],
            }
        )
    return out
