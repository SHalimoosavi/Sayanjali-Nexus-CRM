"""
Central configuration for the Sayanjali Nexus CRM backend.

All environment-dependent values live here. Swapping SQLite -> PostgreSQL
later only means changing DATABASE_URL in .env; no code changes required
because we never use SQLite-specific SQL, only SQLAlchemy Core/ORM.
"""
from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # --- App ---
    APP_NAME: str = "Sayanjali Nexus CRM"
    ENVIRONMENT: str = "local"  # local | staging | production
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Database ---
    # Local-first default. Point this at a postgres:// URL later with zero code changes.
    DATABASE_URL: str = "sqlite:///./data/sayanjali_crm.db"

    # --- Security / Auth ---
    SECRET_KEY: str = Field(default="CHANGE_ME_IN_PRODUCTION_ENV_FILE")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    SESSION_TIMEOUT_MINUTES: int = 60

    # --- CORS (for local Electron/React dev servers) ---
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "app://."]

    # --- Backups ---
    BACKUP_DIR: str = "./backups"
    AUTO_BACKUP_INTERVAL_HOURS: int = 24

    # --- Pagination defaults ---
    DEFAULT_PAGE_SIZE: int = 25
    MAX_PAGE_SIZE: int = 200


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
