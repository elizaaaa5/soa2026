"""
Users Service - микросервис для управления пользователями.

Ответственность:
- Регистрация пользователей
- Аутентификация и авторизация
- Управление профилями
- Управление ролями и правами доступа

Технологический стек: FastAPI + PostgreSQL

На данном этапе реализован только health check endpoint.
Бизнес-логика будет добавлена в будущем.
"""

from fastapi import FastAPI
from pydantic import BaseModel
import os

# Получаем переменные окружения
SERVICE_NAME = os.getenv("SERVICE_NAME", "users-service")
SERVICE_VERSION = os.getenv("SERVICE_VERSION", "1.0.0")

# Инициализация FastAPI приложения
app = FastAPI(
    title=SERVICE_NAME.replace("-", " ").title(),
    description="Users Service - микросервис для управления пользователями",
    version=SERVICE_VERSION,
)


class HealthResponse(BaseModel):
    """Модель ответа health check endpoint"""
    status: str
    service: str
    version: str


@app.get("/")
async def root():
    """Корневой endpoint"""
    return {
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "message": "Users Service is running"
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    """
    Health check endpoint.

    Возвращает статус работоспособности сервиса.
    Используется для мониторинга и load balancing.

    Returns:
        HealthResponse: статус сервиса
    """
    return HealthResponse(
        status="ok",
        service=SERVICE_NAME,
        version=SERVICE_VERSION
    )


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )
