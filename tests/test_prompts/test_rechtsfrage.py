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


def test_rechtsfrage_expands_with_question_only():
    app = create_mcp_app()
    result = _get_prompt(app, "rechtsfrage", {"frage": "Was ist Verbraucherwiderruf?"})
    messages = result.messages
    assert len(messages) == 1
    body = _text(messages[0])
    assert "Verbraucherwiderruf" in body
    assert "list_laws" in body
    assert "legal://" in body


def test_rechtsfrage_includes_rechtsgebiet_when_provided():
    app = create_mcp_app()
    result = _get_prompt(app, "rechtsfrage", {"frage": "X?", "rechtsgebiet": "zivilrecht"})
    body = _text(result.messages[0])
    assert "zivilrecht" in body.lower()
