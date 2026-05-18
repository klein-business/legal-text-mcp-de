# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
"""Tests for cli/_output.py — TTY detection, JSON envelope, error rendering."""

from __future__ import annotations

import io
import json

from legal_text_mcp_de.cli._output import (
    EXIT_CONNECTIVITY,
    EXIT_CORPUS,
    EXIT_RUNTIME,
    EXIT_SAMPLING,
    EXIT_SUCCESS,
    EXIT_USAGE,
    is_json_mode,
    render_data,
    render_error,
)


def test_is_json_mode_explicit_flag_wins():
    assert is_json_mode(force_json=True, stream=io.StringIO()) is True


def test_is_json_mode_pipe_defaults_to_json():
    # StringIO has no isatty() returning True
    assert is_json_mode(force_json=False, stream=io.StringIO()) is True


def test_is_json_mode_tty_defaults_to_text():
    fake_tty = io.StringIO()
    fake_tty.isatty = lambda: True  # type: ignore[method-assign]
    assert is_json_mode(force_json=False, stream=fake_tty) is False


def test_render_data_json_envelope_shape():
    buf = io.StringIO()
    render_data({"law": {"canonical_id": "bgb"}}, stream=buf, force_json=True)
    payload = json.loads(buf.getvalue())
    assert payload == {"data": {"law": {"canonical_id": "bgb"}}, "error": None}


def test_render_error_json_envelope_shape():
    buf = io.StringIO()
    render_error(
        code="NORM_NOT_FOUND",
        message="Norm '§ 999' not found",
        details={"code": "BGB", "norm": "§ 999"},
        stream=buf,
        force_json=True,
    )
    payload = json.loads(buf.getvalue())
    assert payload == {
        "data": None,
        "error": {
            "code": "NORM_NOT_FOUND",
            "message": "Norm '§ 999' not found",
            "details": {"code": "BGB", "norm": "§ 999"},
        },
    }


def test_exit_code_constants_are_unix_conventional():
    assert EXIT_SUCCESS == 0
    assert EXIT_RUNTIME == 1
    assert EXIT_USAGE == 2
    assert EXIT_SAMPLING == 3
    assert EXIT_CORPUS == 4
    assert EXIT_CONNECTIVITY == 5


# --- text-mode coverage ---


def test_render_data_text_mode_uses_default_repr_when_no_renderer():
    """Text mode without text_renderer falls back to Console.print of the payload."""
    fake_tty = io.StringIO()
    fake_tty.isatty = lambda: True  # type: ignore[method-assign]
    from legal_text_mcp_de.cli._output import render_data

    render_data({"hello": "world"}, stream=fake_tty, force_json=False)
    output = fake_tty.getvalue()
    assert "hello" in output
    assert "world" in output


def test_render_data_text_mode_calls_text_renderer_when_provided():
    """When text_renderer is given, it receives (payload, console)."""
    fake_tty = io.StringIO()
    fake_tty.isatty = lambda: True  # type: ignore[method-assign]
    seen = {}

    def renderer(payload, console):
        seen["payload"] = payload
        console.print("custom")

    from legal_text_mcp_de.cli._output import render_data

    render_data({"x": 1}, stream=fake_tty, force_json=False, text_renderer=renderer)
    assert seen["payload"] == {"x": 1}
    assert "custom" in fake_tty.getvalue()


def test_render_error_text_mode_writes_to_stderr_stream():
    """Text-mode error renders into the provided stream with the code + message."""
    err_buf = io.StringIO()
    err_buf.isatty = lambda: True  # type: ignore[method-assign]
    from legal_text_mcp_de.cli._output import render_error

    render_error(
        code="X_ERR",
        message="something broke",
        details={"k": "v"},
        stream=err_buf,
        force_json=False,
    )
    output = err_buf.getvalue()
    assert "X_ERR" in output
    assert "something broke" in output


def test_render_table_emits_columns_and_rows():
    """render_table prints a Rich Table with the given columns + row values."""
    from rich.console import Console

    buf = io.StringIO()
    c = Console(file=buf, width=80)
    from legal_text_mcp_de.cli._output import render_table

    render_table(
        rows=[{"a": "1", "b": "2"}, {"a": "3", "b": "4"}],
        columns=["a", "b"],
        title="T",
        console=c,
    )
    output = buf.getvalue()
    assert "a" in output and "b" in output
    assert "1" in output and "4" in output
