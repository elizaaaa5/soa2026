"""User service."""

from datetime import datetime, timedelta, timezone
from uuid import UUID

from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import get_settings
from src.db.models import User, UserRole, RefreshToken

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserService:
    """Сервис для работы с пользователями."""

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> User | None:
        """Получить пользователя по ID."""
        result = await db.execute(select(User).where(User.id == UUID(user_id)))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> User | None:
        """Получить пользователя по email."""
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def email_exists(db: AsyncSession, email: str) -> bool:
        """Проверить, существует ли email."""
        user = await UserService.get_by_email(db, email)
        return user is not None

    @staticmethod
    async def create(
        db: AsyncSession,
        email: str,
        password: str,
        role: UserRole = UserRole.USER,
    ) -> User:
        """Создать пользователя."""
        user = User(
            email=email,
            password_hash=pwd_context.hash(password),
            role=role,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def authenticate(
        db: AsyncSession,
        email: str,
        password: str,
    ) -> User | None:
        """Аутентифицировать пользователя."""
        user = await UserService.get_by_email(db, email)
        if not user:
            return None
        if not pwd_context.verify(password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user
