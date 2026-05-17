# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Thin SPARQL client for the EUR-Lex Cellar endpoint.

The Cellar SPARQL endpoint resolves CELEX numbers (e.g. 32016R0679 for the
GDPR) to downloadable XML URLs. This client is a thin wrapper that lets
tests inject a fake `query_fn` while production uses SPARQLWrapper against
publications.europa.eu.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


CELLAR_SPARQL = "https://publications.europa.eu/webapi/rdf/sparql"


def _default_query(query: str) -> dict[str, Any]:
    """Real-network default; tests should always inject a fake."""
    from SPARQLWrapper import JSON, SPARQLWrapper  # type: ignore[import-not-found]  # no stubs; lazy import

    wrapper = SPARQLWrapper(CELLAR_SPARQL)
    wrapper.setQuery(query)
    wrapper.setReturnFormat(JSON)
    result: Any = wrapper.queryAndConvert()
    if not isinstance(result, dict):
        raise RuntimeError(f"Unexpected SPARQL response type: {type(result).__name__}")
    return result


@dataclass
class CellarClient:
    """Resolves CELEX numbers to XML URLs via Cellar SPARQL.

    Parameters
    ----------
    query_fn
        ``(sparql_query) -> result_dict`` returning the SPARQL response as
        a JSON-decoded dict. Tests inject a fake; production defaults to
        SPARQLWrapper against the public Cellar endpoint.
    """

    query_fn: Callable[[str], dict[str, Any]] = field(default=_default_query)

    def resolve_xml_url(self, celex: str, lang: str = "DE") -> str:
        """Return the canonical XML download URL for a given CELEX + language.

        Raises ``ValueError`` if Cellar returns no binding for the requested
        CELEX/lang combination — this is treated as a hard error because the
        downstream EU-acts pipeline needs the URL to fetch the act body.
        """
        query = f"""
        PREFIX cdm: <http://publications.europa.eu/ontology/cdm#>
        SELECT ?xmlUrl WHERE {{
          ?work cdm:resource_legal_id_celex "{celex}" .
          ?expr cdm:expression_belongs_to_work ?work ;
                cdm:expression_uses_language <http://publications.europa.eu/resource/authority/language/{lang}> .
          ?manifestation cdm:manifestation_manifests_expression ?expr .
          ?xmlUrl cdm:item_belongs_to_manifestation ?manifestation .
          FILTER(STRENDS(STR(?xmlUrl), ".xml"))
        }} LIMIT 1
        """
        result = self.query_fn(query)
        bindings = result.get("results", {}).get("bindings", [])
        if not bindings:
            raise ValueError(f"No Cellar XML URL for CELEX {celex} lang {lang}")
        return str(bindings[0]["xmlUrl"]["value"])
