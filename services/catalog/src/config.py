"""Configuration settings for Catalog Service."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    service_name: str = "catalog-service"
    port: int = 8002

    database_url: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/catalog_db"
    )

    # JWT
    jwt_secret_key: str = "super-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


settings = Settings()
