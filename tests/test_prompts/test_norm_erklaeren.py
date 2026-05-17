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


def test_norm_erklaeren_contains_code_norm_and_key_terms():
    app = create_mcp_app()
    result = _get_prompt(app, "norm_erklaeren", {"code": "BGB", "norm": "433"})
    messages = result.messages
    assert len(messages) == 1
    body = _text(messages[0])
    assert "BGB" in body
    assert "433" in body
    assert "legal://laws/" in body
    assert "Erklärung" in body
