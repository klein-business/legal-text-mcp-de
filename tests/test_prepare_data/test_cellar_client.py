# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import pytest

from prepare_data.eu_acts.cellar_client import CellarClient


def test_cellar_resolves_celex_to_xml_url():
    fake_sparql_response = {
        "results": {
            "bindings": [
                {"xmlUrl": {"value": "https://eur-lex.europa.eu/legal-content/DE/TXT/XML/?uri=CELEX:32016R0679"}}
            ]
        }
    }
    client = CellarClient(query_fn=lambda q: fake_sparql_response)
    url = client.resolve_xml_url(celex="32016R0679", lang="DE")
    assert url.endswith("CELEX:32016R0679")


def test_cellar_raises_when_no_binding():
    empty = {"results": {"bindings": []}}
    client = CellarClient(query_fn=lambda q: empty)
    with pytest.raises(ValueError, match="No Cellar XML URL for CELEX"):
        client.resolve_xml_url(celex="99999R9999", lang="DE")


def test_cellar_passes_celex_and_lang_into_query():
    captured: list[str] = []

    def capturing_query(q: str) -> dict:
        captured.append(q)
        return {"results": {"bindings": [{"xmlUrl": {"value": "https://example.invalid/x.xml"}}]}}

    client = CellarClient(query_fn=capturing_query)
    client.resolve_xml_url(celex="32024R1689", lang="FR")
    assert len(captured) == 1
    assert "32024R1689" in captured[0]
    assert "FR" in captured[0]
