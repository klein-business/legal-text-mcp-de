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
