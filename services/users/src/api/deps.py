"""Dependencies for API endpoints."""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import ErrorResponse, TokenPayload
from src.db import get_db, User
from src.services import AuthService, UserService

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Получение текущего пользователя из JWT токена."""
    token = credentials.credentials

    # Декодируем токен
    payload = AuthService.decode_token(token)

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="TOKEN_INVALID",
                message="Недействительный токен",
            ).model_dump(),
        )

    # Проверяем срок действия
    from datetime import datetime

    if datetime.utcnow().timestamp() > payload.get("exp", 0):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="TOKEN_EXPIRED",
                message="Токен истёк",
            ).model_dump(),
        )

    # Получаем пользователя
    user = await UserService.get_by_id(db, payload["sub"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="TOKEN_INVALID",
                message="Пользователь не найден",
            ).model_dump(),
        )

    return user


def require_role(*roles: str):
    """Dependency для проверки роли пользователя."""

    async def role_checker(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role.value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    error_code="ACCESS_DENIED",
                    message="Недостаточно прав для выполнения операции",
                ).model_dump(),
            )
        return current_user

    return role_checker
