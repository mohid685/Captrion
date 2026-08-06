"""
Centralized application configuration.

All environment-dependent values (API keys, feature flags) are read here
so the rest of the app never touches os.environ directly.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # Pinecone
    pinecone_api_key: str | None = None
    pinecone_environment: str = "us-east-1"
    pinecone_index_name: str = "financial-advisor"

    # OpenRouter (LLM)
    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-oss-20b:free"

    # External data sources
    alpha_vantage_api_key: str | None = None

    # App
    app_env: str = "development"
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and cached — avoids re-parsing .env every call."""
    return Settings()