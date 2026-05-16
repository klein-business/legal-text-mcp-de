# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 klein-business
from pydantic import ConfigDict
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    model_config = ConfigDict(env_file='.env')

    min_paragraphs: int = 5
    dataset_path: str | None = None
    strict_startup: bool = True
    host: str = '0.0.0.0'
    port: int = 8001
    debug: bool = False
    load_from_github: list[str] | None = None
    load_from_folder: str | None = None

settings = Settings()
