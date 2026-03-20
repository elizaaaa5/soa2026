"""Configuration for Gateway Service"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""

    # Service URLs for routing
    USERS_SERVICE_URL: str = "http://users-service:8001"
    CATALOG_SERVICE_URL: str = "http://catalog-service:8002"
    ORDERS_SERVICE_URL: str = "http://orders-service:8003"

    # JWT Settings
    JWT_SECRET_KEY: str = "your-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"

    # Gateway Settings
    GATEWAY_PORT: int = 8000
    GATEWAY_HOST: str = "0.0.0.0"

    # Public endpoints (no auth required)
    PUBLIC_ENDPOINTS: list[str] = [
        "/auth/register",
        "/auth/login",
        "/auth/refresh",
        "/health",
        "/docs",
        "/openapi.json",
    ]

    class Config:
        env_file = ".env"


settings = Settings()

# Service routing configuration
SERVICE_URLS = {
    "users": settings.USERS_SERVICE_URL,
    "catalog": settings.CATALOG_SERVICE_URL,
    "orders": settings.ORDERS_SERVICE_URL,
}

# Path routing configuration
PATH_ROUTES = {
    "/auth": ("users", "/auth"),
    "/users": ("users", "/users"),
    "/products": ("catalog", "/products"),
    "/orders": ("orders", "/orders"),
    "/promo-codes": ("orders", "/promo-codes"),
}
