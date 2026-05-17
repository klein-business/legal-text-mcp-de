# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pathlib import Path
from unittest.mock import patch

import pytest

from legal_text_mcp_de.corpus.loader import BundleLoadError, LoadedBundle


def test_resolve_dataset_path_returns_explicit_setting(monkeypatch):
    monkeypatch.setenv("DATASET_PATH", "/tmp/my-bundle.tar.zst")
    monkeypatch.setenv("CORPUS_AUTO_DOWNLOAD", "false")
    monkeypatch.setenv("STRICT_STARTUP", "false")

    from legal_text_mcp_de.config import Settings
    from legal_text_mcp_de import server as srv_module

    # Force a fresh Settings instance picking up env
    new_settings = Settings()
    monkeypatch.setattr(srv_module, "settings", new_settings)

    path = srv_module._resolve_dataset_path()
    assert path == Path("/tmp/my-bundle.tar.zst")


def test_resolve_dataset_path_calls_loader_when_unset(monkeypatch):
    monkeypatch.delenv("DATASET_PATH", raising=False)
    monkeypatch.setenv("CORPUS_AUTO_DOWNLOAD", "true")
    monkeypatch.setenv("STRICT_STARTUP", "false")
    monkeypatch.setenv("STRICT_DATASET", "false")

    from legal_text_mcp_de.config import Settings
    from legal_text_mcp_de import server as srv_module

    new_settings = Settings()
    monkeypatch.setattr(srv_module, "settings", new_settings)

    fake = LoadedBundle(bundle_path=Path("/tmp/fake.tar.zst"), source="cache", version="latest")
    with patch("legal_text_mcp_de.server.load_corpus_bundle", return_value=fake) as load:
        path = srv_module._resolve_dataset_path()
    load.assert_called_once()
    assert path == Path("/tmp/fake.tar.zst")


def test_resolve_dataset_path_strict_raises_when_no_options(monkeypatch):
    monkeypatch.delenv("DATASET_PATH", raising=False)
    monkeypatch.setenv("CORPUS_AUTO_DOWNLOAD", "false")
    monkeypatch.setenv("STRICT_STARTUP", "true")

    from legal_text_mcp_de.config import Settings
    from legal_text_mcp_de import server as srv_module

    new_settings = Settings()
    monkeypatch.setattr(srv_module, "settings", new_settings)

    with pytest.raises(BundleLoadError):
        srv_module._resolve_dataset_path()


def test_resolve_dataset_path_returns_none_when_non_strict(monkeypatch):
    monkeypatch.delenv("DATASET_PATH", raising=False)
    monkeypatch.setenv("CORPUS_AUTO_DOWNLOAD", "false")
    monkeypatch.setenv("STRICT_STARTUP", "false")
    monkeypatch.setenv("STRICT_DATASET", "false")

    from legal_text_mcp_de.config import Settings
    from legal_text_mcp_de import server as srv_module

    new_settings = Settings()
    monkeypatch.setattr(srv_module, "settings", new_settings)

    path = srv_module._resolve_dataset_path()
    assert path is None
