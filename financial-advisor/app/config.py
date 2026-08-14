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

    # Postgres (user accounts, profiles, memory)
    postgres_user: str = "advisor"
    postgres_password: str = "advisor_dev_password"
    postgres_db: str = "financial_advisor"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    # JWT auth
    jwt_secret_key: str = "change-this-to-a-long-random-string-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440

    # Voice (Phase 6)
    camb_api_key: str | None = None
    camb_voice_id: int = 170634
    whisper_model_name: str = "openai/whisper-small"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    """Settings are read once and cached — avoids re-parsing .env every call."""
    return Settings()