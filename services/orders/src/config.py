from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/orders_db"
    )

    # API
    API_V1_PREFIX: str = "/api/v1"
    PROJECT_NAME: str = "Orders Service"
    VERSION: str = "1.0.0"

    # Services
    CATALOG_SERVICE_URL: str = "http://localhost:8001"
    USERS_SERVICE_URL: str = "http://localhost:8002"

    # JWT
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Rate limiting
    ORDER_CREATE_COOLDOWN_SECONDS: int = 60

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()
