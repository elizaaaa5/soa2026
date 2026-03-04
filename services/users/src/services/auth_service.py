"""Auth service utilities."""

from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID

from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.models import RefreshToken

settings = get_settings()


class AuthService:
    """Сервис для работы с JWT токенами."""

    @staticmethod
    def create_access_token(user_id: str, role) -> str:
        """Создать access токен."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=settings.access_token_expire_minutes)

        payload = {
            "sub": user_id,
            "role": role.value if hasattr(role, "value") else role,
            "type": "access",
            "exp": expire,
            "iat": now,
        }

        return jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def create_refresh_token(user_id: str) -> str:
        """Создать refresh токен."""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=settings.refresh_token_expire_days)

        payload = {
            "sub": user_id,
            "type": "refresh",
            "exp": expire,
            "iat": now,
        }

        return jwt.encode(
            payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
        )

    @staticmethod
    def decode_token(token: str) -> dict[str, Any] | None:
        """Декодировать токен."""
        try:
            return jwt.decode(
                token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
            )
        except JWTError:
            return None

    @staticmethod
    async def create_refresh_token_record(
        db: AsyncSession,
        user_id: str,
        token: str,
    ) -> RefreshToken:
        """Сохранить refresh токен в БД."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(days=settings.refresh_token_expire_days)

        token_record = RefreshToken(
            user_id=UUID(user_id),
            token=token,
            expires_at=expires_at,
        )
        db.add(token_record)
        await db.commit()
        await db.refresh(token_record)
        return token_record

    @staticmethod
    async def get_refresh_token(
        db: AsyncSession,
        token: str,
    ) -> RefreshToken | None:
        """Получить refresh токен из БД."""
        result = await db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def revoke_refresh_token(
        db: AsyncSession,
        token: str,
    ) -> None:
        """Отозвать refresh токен."""
        token_record = await AuthService.get_refresh_token(db, token)
        if token_record:
            token_record.revoked = True
            await db.commit()
