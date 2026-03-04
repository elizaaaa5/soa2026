"""API схемы (DTO)."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from src.db.models import UserRole


# Base schemas
class ErrorResponse(BaseModel):
    """Стандартный ответ с ошибкой."""

    error_code: str
    message: str
    details: dict[str, Any] | None = None


# Auth schemas
class UserRegister(BaseModel):
    """Запрос на регистрацию."""

    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole = UserRole.USER
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)


class UserLogin(BaseModel):
    """Запрос на вход."""

    email: EmailStr
    password: str


class RefreshTokenRequest(BaseModel):
    """Запрос на обновление токена."""

    refresh_token: str


class AuthResponse(BaseModel):
    """Ответ с токенами."""

    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int


# User schemas
class UserResponse(BaseModel):
    """Ответ с данными пользователя."""

    id: str
    email: str
    role: UserRole
    first_name: str | None = None
    last_name: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


# JWT payload
class TokenPayload(BaseModel):
    """Данные из JWT токена."""

    sub: str
    role: str
    exp: int
    type: str
