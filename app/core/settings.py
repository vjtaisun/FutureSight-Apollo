from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Review Summarizer API"
    app_version: str = "1.0.0"
    log_level: str = "INFO"
    max_csv_size_mb: int = Field(default=10, ge=1, le=100)
    max_rows: int = Field(default=50000, ge=1, le=500000)
    request_timeout_seconds: int = Field(default=20, ge=5, le=120)
    openai_api_key: str | None = None
    openai_model: str = "gpt-4.1-mini"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
