"""Users endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import UserResponse, ErrorResponse
from src.db import get_db
from src.services import UserService
from src.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.get(
    "/me",
    response_model=UserResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Unauthorized"},
    },
)
async def get_current_user_profile(
    current_user=Depends(get_current_user),
):
    """Получение профиля текущего пользователя."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        role=current_user.role,
        created_at=current_user.created_at,
    )
