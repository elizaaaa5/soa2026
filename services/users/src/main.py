"""Users Service - управление пользователями и аутентификация."""

import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api import api_router
from src.config import get_settings
from src.middleware.logging import LoggingMiddleware

settings = get_settings()

app = FastAPI(
    title="Users Service",
    description="API для управления пользователями и аутентификации",
    version=settings.service_version,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Include API routes
app.include_router(api_router)


@app.get("/")
async def root():
    """Корневой endpoint."""
    return {
        "service": settings.service_name,
        "version": settings.service_version,
        "message": "Users Service is running",
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": settings.service_name,
        "version": settings.service_version,
    }


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
