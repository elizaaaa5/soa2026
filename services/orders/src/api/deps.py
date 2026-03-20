"""Dependencies for orders API endpoints."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError
import uuid

from src.config import get_settings

security = HTTPBearer()
settings = get_settings()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """Get current user from JWT token."""
    token = credentials.credentials

    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "TOKEN_INVALID",
                "message": "Invalid token",
            },
        )

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "TOKEN_INVALID",
                "message": "Invalid token",
            },
        )

    # Check expiration
    from datetime import datetime, timezone

    if datetime.now(timezone.utc).timestamp() > payload.get("exp", 0):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error_code": "TOKEN_EXPIRED",
                "message": "Token expired",
            },
        )

    # Set user_id in request state for logging middleware
    request.state.user_id = payload["sub"]

    # Return user info (id and role)
    return {
        "id": payload["sub"],
        "role": payload.get("role", "USER"),
    }


def require_role(*roles: str):
    """Dependency to check user role."""

    async def role_checker(
        current_user: dict = Depends(get_current_user),
    ) -> dict:
        if current_user["role"] not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "ACCESS_DENIED",
                    "message": "Insufficient permissions",
                },
            )
        return current_user

    return role_checker
