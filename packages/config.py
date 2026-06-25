"""Centralized environment-backed configuration for OpenStock AI.

All secrets and connection strings must come from environment variables
(see `.env.example`). No module outside this file should read API keys
directly from `os.environ`.
"""
from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: str = "local"

    database_url: str = "sqlite:///./openstock_ai.db"
    redis_url: str | None = None

    openai_api_key: str | None = None
    anthropic_api_key: str | None = None
    google_api_key: str | None = None
    deepseek_api_key: str | None = None
    qwen_api_key: str | None = None

    alpha_vantage_api_key: str | None = None
    finnhub_api_key: str | None = None
    polygon_api_key: str | None = None
    fred_api_key: str | None = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
