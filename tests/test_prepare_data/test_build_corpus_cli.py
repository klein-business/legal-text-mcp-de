# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path

from prepare_data.build_corpus import main


def test_build_corpus_with_no_real_sources_writes_empty_bundle(tmp_path: Path, monkeypatch):
    out = tmp_path / "corpus.tar.zst"
    monkeypatch.setattr("prepare_data.build_corpus._collect_bund_laws", lambda: [])
    monkeypatch.setattr("prepare_data.build_corpus._collect_state_laws", lambda codes: [])
    monkeypatch.setattr("prepare_data.build_corpus._collect_eu_acts", lambda celexes: [])

    rc = main(["--output", str(out), "--sources", "bund"])
    assert rc == 0
    assert out.exists()


def test_build_corpus_rejects_missing_required_args():
    import pytest

    with pytest.raises(SystemExit):
        main(["--sources", "bund"])  # missing --output


def test_unimplemented_federal_source_fails_without_writing_empty_bundle(tmp_path, capsys):
    import pytest

    out = tmp_path / "corpus.tar.zst"
    with pytest.raises(SystemExit) as exc:
        main(["--output", str(out), "--sources", "bund"])
    assert exc.value.code == 2
    assert not out.exists()
    assert "not implemented" in capsys.readouterr().err
