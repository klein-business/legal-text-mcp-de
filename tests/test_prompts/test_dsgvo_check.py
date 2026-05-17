# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
import asyncio

from legal_text_mcp_de.server import create_mcp_app


def _get_prompt(app, name, args):
    try:
        result = app.get_prompt(name, args)
    except TypeError:
        result = asyncio.get_event_loop().run_until_complete(app.get_prompt(name, args))
    if asyncio.iscoroutine(result):
        result = asyncio.get_event_loop().run_until_complete(result)
    return result


def _text(msg):
    c = msg.content
    return c.text if hasattr(c, "text") else str(c)


def test_dsgvo_check_contains_aktivitaet_and_key_articles():
    app = create_mcp_app()
    result = _get_prompt(app, "dsgvo_check", {"aktivitaet": "E-Mail-Marketing mit Opt-in"})
    messages = result.messages
    assert len(messages) == 1
    body = _text(messages[0])
    assert "E-Mail-Marketing mit Opt-in" in body
    assert "Art. 5" in body
    assert "Art. 6" in body
    assert "Art. 13" in body
