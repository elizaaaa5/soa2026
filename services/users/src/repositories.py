"""Репозиторий для работы с пользователями."""

from datetime import datetime, timedelta, timezone
from typing import TypeVar
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import User, UserRole, RefreshToken, UserOperation

ModelType = TypeVar("ModelType", bound=User)


class UserRepository:
    """Репозиторий для работы с пользователями."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user: User) -> User:
        """Создать пользователя."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Получить пользователя по ID."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> User | None:
        """Получить пользователя по email."""
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def update(self, user: User) -> User:
        """Обновить пользователя."""
        await self.db.commit()
        await self.db.refresh(user)
        return user


class RefreshTokenRepository:
    """Репозиторий для работы с refresh токенами."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, token: RefreshToken) -> RefreshToken:
        """Создать refresh токен."""
        self.db.add(token)
        await self.db.commit()
        await self.db.refresh(token)
        return token

    async def get_by_token(self, token: str) -> RefreshToken | None:
        """Получить токен по значению."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.token == token)
        )
        return result.scalar_one_or_none()

    async def revoke_all_for_user(self, user_id: UUID) -> None:
        """Отозвать все токены пользователя."""
        result = await self.db.execute(
            select(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        tokens = result.scalars().all()
        for token in tokens:
            token.revoked = True
        await self.db.commit()

    async def revoke(self, token: RefreshToken) -> None:
        """Отозвать токен."""
        token.revoked = True
        await self.db.commit()


class UserOperationRepository:
    """Репозиторий для отслеживания операций пользователя."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, operation: UserOperation) -> UserOperation:
        """Создать запись об операции."""
        self.db.add(operation)
        await self.db.commit()
        await self.db.refresh(operation)
        return operation

    async def get_last_operation(
        self, user_id: UUID, operation_type: str
    ) -> UserOperation | None:
        """Получить последнюю операцию пользователя указанного типа."""
        result = await self.db.execute(
            select(UserOperation)
            .where(UserOperation.user_id == user_id)
            .where(UserOperation.operation_type == operation_type)
            .order_by(UserOperation.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def can_perform_operation(
        self, user_id: UUID, operation_type: str, rate_limit_minutes: int
    ) -> bool:
        """Проверить, может ли пользователь выполнить операцию (rate limiting)."""
        last_op = await self.get_last_operation(user_id, operation_type)
        if last_op is None:
            return True

        now = datetime.now(timezone.utc)
        time_since_last = now - last_op.created_at
        return time_since_last >= timedelta(minutes=rate_limit_minutes)
