from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from datetime import datetime

from src.db.session import get_db
from src.db.models import PromoCode, DiscountType
from src.api.schemas import PromoCodeCreate, PromoCodeResponse

router = APIRouter()


@router.post("", response_model=PromoCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_promo_code(
    promo_data: PromoCodeCreate,
    db: AsyncSession = Depends(get_db),
):
    """Создание промокода"""
    # Check if code already exists
    result = await db.execute(
        select(PromoCode).where(PromoCode.code == promo_data.code)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "PROMO_CODE_EXISTS",
                "message": "Промокод уже существует",
            },
        )

    # Validate dates
    if promo_data.valid_from >= promo_data.valid_until:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_DATES",
                "message": "valid_until должен быть позже valid_from",
            },
        )

    # Create promo code
    promo_code = PromoCode(
        code=promo_data.code,
        discount_type=promo_data.discount_type,
        discount_value=promo_data.discount_value,
        min_order_amount=promo_data.min_order_amount,
        max_uses=promo_data.max_uses,
        current_uses=0,
        valid_from=promo_data.valid_from,
        valid_until=promo_data.valid_until,
        active=True,
    )

    db.add(promo_code)
    await db.commit()
    await db.refresh(promo_code)

    return PromoCodeResponse(
        id=promo_code.id,
        code=promo_code.code,
        discount_type=promo_code.discount_type,
        discount_value=float(promo_code.discount_value),
        min_order_amount=float(promo_code.min_order_amount),
        max_uses=promo_code.max_uses,
        current_uses=promo_code.current_uses,
        valid_from=promo_code.valid_from,
        valid_until=promo_code.valid_until,
        active=promo_code.active,
    )
