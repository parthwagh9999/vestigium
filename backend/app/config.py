"""Application configuration using Pydantic Settings.

All configuration is loaded from environment variables with sensible defaults
for local development. Production deployments should use .env files or
container environment variables.
"""

from __future__ import annotations

import secrets
from enum import Enum
from pathlib import Path
from typing import Any

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- Application ----
    app_name: str = "VESTIGIUM"
    app_env: Environment = Environment.DEVELOPMENT
    app_debug: bool = True
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    app_secret_key: str = secrets.token_urlsafe(32)
    app_cors_origins: str = "http://localhost:5173,http://localhost:3000"
    app_version: str = "1.1"

    # ---- Database ----
    database_url: str = "sqlite+aiosqlite:///./vestigium.db"

    # ---- Authentication ----
    jwt_secret_key: str = secrets.token_urlsafe(32)
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7

    # ---- Redis ----
    redis_url: str = ""

    # ---- Celery ----
    celery_broker_url: str = ""
    celery_result_backend: str = ""

    # ---- File Storage ----
    upload_dir: str = "./uploads"
    backup_dir: str = "./backups"
    max_upload_size_mb: int = 100

    # ---- Encryption ----
    encryption_key: str = ""

    # ---- Rate Limiting ----
    rate_limit_requests_per_minute: int = 120
    rate_limit_burst: int = 20

    # ---- Logging ----
    log_level: str = "INFO"
    log_format: str = "json"

    # ---- AI Features ----
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_model: str = "gpt-4"

    # ---- Plugin System ----
    plugin_dir: str = "./plugins"
    plugin_marketplace_url: str = ""

    # ---- Backup ----
    auto_backup_enabled: bool = True
    auto_backup_interval_hours: int = 6
    auto_backup_retention_days: int = 30

    @property
    def cors_origins(self) -> list[str]:
        """Parse CORS origins from comma-separated string."""
        return [origin.strip() for origin in self.app_cors_origins.split(",") if origin.strip()]

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.app_env == Environment.TESTING

    @property
    def has_redis(self) -> bool:
        """Check if Redis is configured."""
        return bool(self.redis_url)

    @property
    def has_celery(self) -> bool:
        """Check if Celery is configured."""
        return bool(self.celery_broker_url)

    @property
    def upload_path(self) -> Path:
        """Get the upload directory as a Path object."""
        path = Path(self.upload_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def backup_path(self) -> Path:
        """Get the backup directory as a Path object."""
        path = Path(self.backup_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def plugin_path(self) -> Path:
        """Get the plugin directory as a Path object."""
        path = Path(self.plugin_dir)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str) -> str:
        """Ensure database URL is properly formatted."""
        valid_prefixes = (
            "sqlite",
            "sqlite+aiosqlite",
            "postgresql",
            "postgresql+asyncpg",
        )
        if not any(v.startswith(prefix) for prefix in valid_prefixes):
            msg = f"Unsupported database URL scheme. Must start with one of: {valid_prefixes}"
            raise ValueError(msg)
        return v


def get_settings() -> Settings:
    """Create and return application settings singleton.

    Returns:
        Settings instance loaded from environment.
    """
    return Settings()
