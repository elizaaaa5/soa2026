"""Конфигурация Users Service."""

from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки сервиса."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Service
    service_name: str = "users-service"
    service_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8001

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/users_db"
    database_echo: bool = False

    # JWT
    jwt_secret_key: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7

    # Rate limiting
    rate_limit_minutes: int = 5


@lru_cache
def get_settings() -> Settings:
    """Получить настройки (singleton)."""
    return Settings()
