"""Auth endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    UserRegister,
    UserLogin,
    RefreshTokenRequest,
    AuthResponse,
    ErrorResponse,
)
from src.db import get_db, User
from src.services import AuthService, UserService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse, "description": "Validation error"},
        409: {"model": ErrorResponse, "description": "User already exists"},
    },
)
async def register(
    data: UserRegister,
    db: AsyncSession = Depends(get_db),
):
    """Регистрация пользователя."""
    # Проверяем, что email не занят
    if await UserService.email_exists(db, data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error_code="USER_ALREADY_EXISTS",
                message="Пользователь с таким email уже существует",
            ).model_dump(),
        )

    # Создаем пользователя
    user = await UserService.create(
        db=db,
        email=data.email,
        password=data.password,
        role=data.role,
    )

    # Генерируем токены
    access_token = AuthService.create_access_token(str(user.id), user.role)
    refresh_token = AuthService.create_refresh_token(str(user.id))

    # Сохраняем refresh токен
    await AuthService.create_refresh_token_record(db, str(user.id), refresh_token)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,  # 30 минут
    )


@router.post(
    "/login",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid credentials"},
    },
)
async def login(
    data: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    """Аутентификация пользователя."""
    user = await UserService.authenticate(db, data.email, data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="INVALID_CREDENTIALS",
                message="Неверный email или пароль",
            ).model_dump(),
        )

    # Генерируем токены
    access_token = AuthService.create_access_token(str(user.id), user.role)
    refresh_token = AuthService.create_refresh_token(str(user.id))

    # Сохраняем refresh токен
    await AuthService.create_refresh_token_record(db, str(user.id), refresh_token)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,
    )


@router.post(
    "/refresh",
    response_model=AuthResponse,
    responses={
        401: {"model": ErrorResponse, "description": "Invalid refresh token"},
    },
)
async def refresh(
    data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Обновление access токена."""
    # Декодируем токен
    payload = AuthService.decode_token(data.refresh_token)

    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="REFRESH_TOKEN_INVALID",
                message="Недействительный refresh токен",
            ).model_dump(),
        )

    # Проверяем токен в БД
    token_record = await AuthService.get_refresh_token(db, data.refresh_token)

    if not token_record or token_record.revoked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="REFRESH_TOKEN_INVALID",
                message="Недействительный или отозванный refresh токен",
            ).model_dump(),
        )

    # Получаем пользователя
    user = await UserService.get_by_id(db, payload["sub"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                error_code="REFRESH_TOKEN_INVALID",
                message="Пользователь не найден",
            ).model_dump(),
        )

    # Отзываем старый токен
    await AuthService.revoke_refresh_token(db, data.refresh_token)

    # Генерируем новые токены
    access_token = AuthService.create_access_token(str(user.id), user.role)
    refresh_token = AuthService.create_refresh_token(str(user.id))

    # Сохраняем новый refresh токен
    await AuthService.create_refresh_token_record(db, str(user.id), refresh_token)

    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=30 * 60,
    )
