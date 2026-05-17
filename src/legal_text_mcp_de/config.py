# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    min_paragraphs: int = 5
    dataset_path: str | None = None
    strict_startup: bool = True
    host: str = "0.0.0.0"
    port: int = 8001
    debug: bool = False
    load_from_github: list[str] | None = None
    load_from_folder: str | None = None
    corpus_version: str = "latest"
    corpus_auto_download: bool = True
    corpus_cert_identity: str | None = None
    strict_dataset: bool = False
    # Defence-in-depth body-size cap at the application layer. The
    # operator's reverse proxy is expected to enforce its own limit;
    # this is the second line. 1 MiB covers every legitimate request
    # the HTTP API serves (query strings, citation paths) with room
    # to spare.
    max_request_body_bytes: int = 1_048_576


settings = Settings()
