"""API схемы (DTO).

NOTE: Most schemas have been replaced by generated models in src.api.generated.models
Only TokenPayload remains as it's used internally for JWT token handling.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, EmailStr, Field

from src.db.models import UserRole


# REPLACED BY GENERATED MODELS - Use src.api.generated.models.ErrorResponse instead
# class ErrorResponse(BaseModel):
#     """Стандартный ответ с ошибкой."""
#
#     error_code: str
#     message: str
#     details: dict[str, Any] | None = None


# Auth schemas - REPLACED BY GENERATED MODELS
# class UserRegister(BaseModel):
#     """Запрос на регистрацию."""
#
#     email: EmailStr
#     password: str = Field(..., min_length=8)
#     role: UserRole = UserRole.USER
#     first_name: str | None = Field(None, max_length=100)
#     last_name: str | None = Field(None, max_length=100)


# class UserLogin(BaseModel):
#     """Запрос на вход."""
#
#     email: EmailStr
#     password: str


# REPLACED BY GENERATED MODELS - Use src.api.generated.models.RefreshToken instead
# class RefreshTokenRequest(BaseModel):
#     """Запрос на обновление токена."""
#
#     refresh_token: str


# class AuthResponse(BaseModel):
#     """Ответ с токенами."""
#
#     access_token: str
#     refresh_token: str
#     token_type: str = "Bearer"
#     expires_in: int


# User schemas - REPLACED BY GENERATED MODELS
# class UserResponse(BaseModel):
#     """Ответ с данными пользователя."""
#
#     id: str
#     email: str
#     role: UserRole
#     first_name: str | None = None
#     last_name: str | None = None
#     created_at: datetime
#
#     class Config:
#         from_attributes = True


# JWT payload - kept as it's used internally for JWT token handling
class TokenPayload(BaseModel):
    """Данные из JWT токена."""

    sub: str
    role: str
    exp: int
    type: str
