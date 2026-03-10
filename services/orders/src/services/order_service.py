from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from typing import List, Optional
import uuid
from datetime import datetime, timedelta

from src.db.models import Order, OrderItem, OrderStatus, UserOperation, OperationType
from src.config import get_settings

settings = get_settings()


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_rate_limit(self, user_id: uuid.UUID, operation_type: OperationType):
        """Проверка rate limiting"""
        cooldown = timedelta(seconds=settings.ORDER_CREATE_COOLDOWN_SECONDS)
        cutoff_time = datetime.utcnow() - cooldown

        result = await self.db.execute(
            select(UserOperation).where(
                and_(
                    UserOperation.user_id == user_id,
                    UserOperation.operation_type == operation_type,
                    UserOperation.created_at > cutoff_time,
                )
            )
        )
        recent_operation = result.scalar_one_or_none()

        if recent_operation:
            from fastapi import HTTPException, status
            from src.api.schemas import ErrorResponse

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=ErrorResponse(
                    error_code="ORDER_LIMIT_EXCEEDED",
                    message="Превышен лимит частоты создания/обновления заказа",
                ).model_dump(),
            )

    async def check_active_orders(self, user_id: uuid.UUID):
        """Проверка активных заказов"""
        result = await self.db.execute(
            select(Order).where(
                and_(
                    Order.user_id == user_id,
                    Order.status.in_(
                        [OrderStatus.CREATED, OrderStatus.PAYMENT_PENDING]
                    ),
                )
            )
        )
        active_order = result.scalar_one_or_none()

        if active_order:
            from fastapi import HTTPException, status
            from src.api.schemas import ErrorResponse

            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse(
                    error_code="ORDER_HAS_ACTIVE",
                    message="У пользователя уже есть активный заказ",
                ).model_dump(),
            )

    async def validate_products(self, items: List) -> List[dict]:
        """Валидация товаров и остатков"""
        import httpx
        from fastapi import HTTPException, status
        from src.api.schemas import ErrorResponse

        product_ids = [str(item.product_id) for item in items]

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CATALOG_SERVICE_URL}/products/batch",
                json=product_ids,
                timeout=10.0,
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Catalog service unavailable",
                )

            products_data = response.json()

        # Build product map
        product_map = {p["id"]: p for p in products_data}

        # Validate products
        validated_products = []
        insufficient_stock = []

        for item in items:
            product_id_str = str(item.product_id)
            product = product_map.get(product_id_str)

            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=ErrorResponse(
                        error_code="PRODUCT_NOT_FOUND",
                        message=f"Товар {item.product_id} не найден",
                    ).model_dump(),
                )

            if product.get("status") != "ACTIVE":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=ErrorResponse(
                        error_code="PRODUCT_INACTIVE",
                        message=f"Товар {item.product_id} неактивен",
                    ).model_dump(),
                )

            stock = product.get("stock", 0)
            if stock < item.quantity:
                insufficient_stock.append(
                    {
                        "product_id": str(item.product_id),
                        "requested": item.quantity,
                        "available": stock,
                    }
                )

            validated_products.append(
                {
                    "id": item.product_id,
                    "name": product.get("name"),
                    "price": product.get("price", 0),
                    "stock": stock,
                    "quantity": item.quantity,
                }
            )

        if insufficient_stock:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=ErrorResponse(
                    error_code="INSUFFICIENT_STOCK",
                    message="Недостаточно товара на складе",
                    details={"items": insufficient_stock},
                ).model_dump(),
            )

        return validated_products

    async def reserve_stock(self, product_id: uuid.UUID, quantity: int):
        """Резервирование остатков"""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CATALOG_SERVICE_URL}/products/{product_id}/reserve",
                json={"quantity": quantity},
                timeout=10.0,
            )

            if response.status_code != 200:
                raise Exception(f"Failed to reserve stock for product {product_id}")

    async def restore_stock(self, product_id: uuid.UUID, quantity: int):
        """Восстановление остатков"""
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{settings.CATALOG_SERVICE_URL}/products/{product_id}/restore",
                json={"quantity": quantity},
                timeout=10.0,
            )

            if response.status_code != 200:
                # Log error but don't fail the operation
                pass

    async def get_order(self, order_id: uuid.UUID) -> Order:
        """Получение заказа"""
        from fastapi import HTTPException, status
        from src.api.schemas import ErrorResponse

        result = await self.db.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()

        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=ErrorResponse(
                    error_code="ORDER_NOT_FOUND",
                    message="Заказ не найден",
                ).model_dump(),
            )

        return order
