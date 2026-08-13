"""
HHMS Configuration Settings
===========================

Centralized application configuration.

All configuration is loaded from environment variables or the .env file.

Project : Hospital Homoeopathic Management System (HHMS)
Author  : Dr. Sohil Momin
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
import secrets

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.config.runtime_paths import (
    application_root,
    database_path,
    logs_directory,
    secret_key_path,
)


ROOT_DIR = application_root()


def _load_or_create_secret_key() -> str:
    """Load a persistent local secret or generate one on first startup."""
    path = secret_key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        value = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        value = ""
    if value:
        return value
    value = secrets.token_urlsafe(48)
    path.write_text(value + "\n", encoding="utf-8")
    return value


class Settings(BaseSettings):
    """
    Global application settings.

    Every configuration value must originate from
    environment variables or the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=str(application_root() / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ==========================================================
    # Application
    # ==========================================================

    APP_NAME: str = Field(
        default="Hospital Homoeopathic Management System",
        description="Full application name.",
    )

    APP_SHORT_NAME: str = Field(
        default="HHMS",
    )

    APP_VERSION: str = Field(
        default="0.1.0",
    )

    API_V1_PREFIX: str = Field(
        default="/api/v1",
    )

    ENVIRONMENT: str = Field(
        default="development",
    )

    DEBUG: bool = Field(
        default=False,
    )

    SERVER_HOST: str = Field(default="0.0.0.0")
    SERVER_PORT: int = Field(default=8000, ge=1, le=65535)

    # ==========================================================
    # Security
    # ==========================================================

    SECRET_KEY: str = Field(
        default_factory=lambda: _load_or_create_secret_key(),
        description="JWT secret key. Persisted locally when no environment value is supplied.",
    )

    JWT_ALGORITHM: str = Field(
        default="HS256",
    )

    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30,
        ge=1,
    )

    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_URL: str = Field(
        default_factory=lambda: f"sqlite+aiosqlite:///{database_path().as_posix()}",
        description="Database connection URL. Defaults to portable SQLite; may be overridden for PostgreSQL deployments.",
    )

    DATABASE_ECHO: bool = Field(
        default=False,
    )

    # ==========================================================
    # WHO ICD-11
    # ==========================================================

    WHO_ICD11_CLIENT_ID: str | None = Field(default=None)
    WHO_ICD11_CLIENT_SECRET: str | None = Field(default=None)
    WHO_ICD11_API_BASE_URL: str = Field(default="https://id.who.int")
    WHO_ICD11_TOKEN_URL: str = Field(
        default="https://icdaccessmanagement.who.int/connect/token"
    )
    WHO_ICD11_RELEASE: str = Field(default="2026-01")

    # ==========================================================
    # Logging
    # ==========================================================

    LOG_LEVEL: str = Field(
        default="INFO",
    )

    LOG_DIRECTORY: str = Field(
        default_factory=lambda: str(logs_directory()),
    )

    LOG_FILE_NAME: str = Field(
        default="hhms.log",
    )

    # ==========================================================
    # CORS
    # ==========================================================

    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://localhost:5173",
        ]
    )

    # ==========================================================
    # Pagination
    # ==========================================================

    DEFAULT_PAGE_SIZE: int = Field(
        default=20,
        ge=1,
        le=500,
    )

    MAX_PAGE_SIZE: int = Field(
        default=100,
        ge=1,
        le=1000,
    )

    # ==========================================================
    # Hospital
    # ==========================================================

    HOSPITAL_NAME: str = Field(
        default="Hospital Homoeopathic Management System",
    )

    HOSPITAL_CODE: str = Field(
        default="HHMS",
    )

    TIME_ZONE: str = Field(
        default="Asia/Kolkata",
    )

    DATE_FORMAT: str = Field(
        default="%Y-%m-%d",
    )

    DATETIME_FORMAT: str = Field(
        default="%Y-%m-%d %H:%M:%S",
    )

    # ==========================================================
    # Paths
    # ==========================================================

    ROOT_DIR: Path = ROOT_DIR

    @property
    def log_path(self) -> Path:
        """Return the full log file path."""
        return self.ROOT_DIR / self.LOG_DIRECTORY / self.LOG_FILE_NAME


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Return the cached application settings instance.

    Returns
    -------
    Settings
        Singleton configuration object loaded from the
        environment and `.env` file.
    """
    return Settings()

