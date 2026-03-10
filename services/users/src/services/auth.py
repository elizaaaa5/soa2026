"""Сервис аутентификации."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

import bcrypt
from jose import jwt, JWTError

from src.config import get_settings
from src.db.models import User, UserRole, RefreshToken, UserOperation
from src.repositories import (
    UserRepository,
    RefreshTokenRepository,
    UserOperationRepository,
)

settings = get_settings()


class AuthService:
    """Сервис аутентификации."""

    def __init__(
        self,
        user_repo: UserRepository,
        token_repo: RefreshTokenRepository,
        operation_repo: UserOperationRepository,
    ):
        self.user_repo = user_repo
        self.token_repo = token_repo
        self.operation_repo = operation_repo

    @staticmethod
    def hash_password(password: str) -> str:
        """Хешировать пароль."""
        password_bytes = password.encode("utf-8")
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password_bytes, salt).decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Проверить пароль."""
        password_bytes = plain_password.encode("utf-8")
        stored_hash = hashed_password.encode("utf-8")
        return bcrypt.checkpw(password_bytes, stored_hash)

    def create_access_token(self, user_id: UUID, role: UserRole) -> str:
        """Создать access токен."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

        payload = {
            "sub": str(user_id),
            "role": role.value,
            "type": "access",
            "exp": expire,
            "iat": now,
        }

        return jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

    def create_refresh_token(self, user_id: UUID) -> str:
        """Создать refresh токен."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.refresh_token_expire_days)

        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "iat": now,
        }

        return jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

    def decode_token(self, token: str) -> dict[str, Any] | None:
        """Декодировать токен."""
        try:
            return jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
        except JWTError:
            return None

    async def register(
        self, email: str, password: str, role: UserRole = UserRole.USER
    ) -> User:
        """Зарегистрировать пользователя."""
        # Проверяем, что пользователь не существует
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ValueError("USER_ALREADY_EXISTS")

        # Создаем пользователя
        user = User(
            email=email,
            password_hash=self.hash_password(password),
            role=role,
        )
        return await self.user_repo.create(user)

    async def login(self, email: str, password: str) -> tuple[User, str, str]:
        """
        Аутентифицировать пользователя.

        Returns:
            Кортеж (user, access_token, refresh_token)
        """
        user = await self.user_repo.get_by_email(email)
        if not user:
            raise ValueError("INVALID_CREDENTIALS")

        if not self.verify_password(password, user.password_hash):
            raise ValueError("INVALID_CREDENTIALS")

        if not user.is_active:
            raise ValueError("USER_INACTIVE")

        # Создаем токены
        access_token = self.create_access_token(user.id, user.role)
        refresh_token = self.create_refresh_token(user.id)

        # Сохраняем refresh токен в БД
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.refresh_token_expire_days)
        token_record = RefreshToken(
            user_id=user.id,
            token=refresh_token,
            expires_at=expires_at,
        )
        await self.token_repo.create(token_record)

        return user, access_token, refresh_token

    async def refresh(self, refresh_token: str) -> tuple[str, str]:
        """
        Обновить токены.

        Returns:
            Кортеж (new_access_token, new_refresh_token)
        """
        # Проверяем токен в БД
        token_record = await self.token_repo.get_by_token(refresh_token)
        if not token_record:
            raise ValueError("REFRESH_TOKEN_INVALID")

        if token_record.revoked:
            raise ValueError("REFRESH_TOKEN_INVALID")

        if token_record.expires_at < datetime.now(timezone.utc):
            raise ValueError("REFRESH_TOKEN_INVALID")

        # Получаем пользователя
        user = await self.user_repo.get_by_id(token_record.user_id)
        if not user or not user.is_active:
            raise ValueError("REFRESH_TOKEN_INVALID")

        # Отзываем старый токен
        await self.token_repo.revoke(token_record)

        # Создаем новые токены
        new_access_token = self.create_access_token(user.id, user.role)
        new_refresh_token = self.create_refresh_token(user.id)

        # Сохраняем новый refresh токен
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.refresh_token_expire_days)
        new_token_record = RefreshToken(
            user_id=user.id,
            token=new_refresh_token,
            expires_at=expires_at,
        )
        await self.token_repo.create(new_token_record)

        return new_access_token, new_refresh_token

    async def validate_access_token(self, token: str) -> dict[str, Any]:
        """Валидировать access токен."""
        payload = self.decode_token(token)
        if not payload:
            raise ValueError("TOKEN_INVALID")

        if payload.get("type") != "access":
            raise ValueError("TOKEN_INVALID")

        user_id = UUID(payload.get("sub"))
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise ValueError("TOKEN_INVALID")

        return payload
