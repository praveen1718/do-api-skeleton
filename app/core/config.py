"""Application configuration, loaded from environment variables.

Twelve-factor style: all config comes from the environment, with sane
defaults for local dev. Never hardcode secrets.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="APP_", extra="ignore")

    # Service identity
    app_name: str = "ingestion-api"
    environment: str = "local"  # local | staging | production
    log_level: str = "INFO"

    # HTTP
    host: str = "0.0.0.0"
    port: int = 8080

    # Ingestion limits (tune to the real challenge spec on the day)
    max_batch_size: int = 1000
    max_payload_bytes: int = 5 * 1024 * 1024  # 5 MiB

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


@lru_cache
def get_settings() -> Settings:
    """Cached so we build Settings once per process."""
    return Settings()
