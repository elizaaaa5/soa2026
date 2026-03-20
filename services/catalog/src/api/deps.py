"""Dependencies for API endpoints."""

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.generated.models import ErrorResponse
from src.db.session import get_session
from src.db.models import Product

security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Get current user from JWT token."""
    token = credentials.credentials

    # Decode token
    from jose import jwt, JWTError
    from src.config import settings

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="TOKEN_INVALID",
                message="Invalid token",
                details=None,
            ).model_dump(),
        )

    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="TOKEN_INVALID",
                message="Invalid token",
                details=None,
            ).model_dump(),
        )

    # Check expiration
    from datetime import datetime, timezone

    if datetime.now(timezone.utc).timestamp() > payload.get("exp", 0):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="TOKEN_EXPIRED",
                message="Token expired",
                details=None,
            ).model_dump(),
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
                detail=ErrorResponse(
                    error_code="ACCESS_DENIED",
                    message="Insufficient permissions",
                    details=None,
                ).model_dump(),
            )
        return current_user

    return role_checker
