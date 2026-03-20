from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timezone
from decimal import Decimal

from src.db.models import PromoCode, DiscountType
from fastapi import HTTPException, status
from src.api.schemas import ErrorResponse


class PromoService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_active_promo_code(self, code: str) -> PromoCode:
        """Получение активного промокода"""
        result = await self.db.execute(select(PromoCode).where(PromoCode.code == code))
        promo_code = result.scalar_one_or_none()

        if not promo_code:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse(
                    error_code="PROMO_CODE_INVALID",
                    message="Промокод не найден, истёк, исчерпан или неактивен",
                ).model_dump(),
            )

        # Validate promo code
        now = datetime.now(timezone.utc)

        if not promo_code.active:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse(
                    error_code="PROMO_CODE_INVALID",
                    message="Промокод не найден, истёк, исчерпан или неактивен",
                ).model_dump(),
            )

        if promo_code.current_uses >= promo_code.max_uses:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse(
                    error_code="PROMO_CODE_INVALID",
                    message="Промокод не найден, истёк, исчерпан или неактивен",
                ).model_dump(),
            )

        if now < promo_code.valid_from or now > promo_code.valid_until:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse(
                    error_code="PROMO_CODE_INVALID",
                    message="Промокод не найден, истёк, исчерпан или неактивен",
                ).model_dump(),
            )

        return promo_code

    async def get_promo_code_by_id(self, promo_code_id) -> PromoCode:
        """Получение промокода по ID"""
        result = await self.db.execute(
            select(PromoCode).where(PromoCode.id == promo_code_id)
        )
        return result.scalar_one_or_none()

    async def calculate_discount(
        self, promo_code: PromoCode, total_amount: Decimal
    ) -> Decimal:
        """Расчет скидки"""
        # Check minimum order amount
        if total_amount < promo_code.min_order_amount:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=ErrorResponse(
                    error_code="PROMO_CODE_MIN_AMOUNT",
                    message="Сумма заказа ниже минимальной для промокода",
                ).model_dump(),
            )

        if promo_code.discount_type == DiscountType.PERCENTAGE:
            discount = total_amount * promo_code.discount_value / Decimal("100")
            # Max 70% discount
            max_discount = total_amount * Decimal("0.7")
            discount = min(discount, max_discount)
        else:  # FIXED_AMOUNT
            discount = min(promo_code.discount_value, total_amount)

        return discount

    async def increment_usage(self, promo_code_id):
        """Увеличение счетчика использований"""
        await self.db.execute(
            update(PromoCode)
            .where(PromoCode.id == promo_code_id)
            .values(current_uses=PromoCode.current_uses + 1)
        )

    async def decrement_usage(self, promo_code_id):
        """Уменьшение счетчика использований"""
        await self.db.execute(
            update(PromoCode)
            .where(PromoCode.id == promo_code_id)
            .values(current_uses=PromoCode.current_uses - 1)
        )
