from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List
import uuid

from src.db.session import get_db
from src.db.models import Order, OrderItem, OrderStatus, UserOperation, OperationType
from src.api.schemas import (
    OrderCreate,
    OrderUpdate,
    OrderResponse,
    OrderItemResponse,
    ErrorResponse,
)
from src.services.order_service import OrderService
from src.services.promo_service import PromoService

router = APIRouter()


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    order_data: OrderCreate,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Создание заказа"""
    order_service = OrderService(db)
    promo_service = PromoService(db)

    # Rate limiting check
    await order_service.check_rate_limit(user_id, OperationType.CREATE_ORDER)

    # Check for active orders
    await order_service.check_active_orders(user_id)

    # Validate products and stock
    product_info = await order_service.validate_products(order_data.items)

    # Calculate totals
    subtotal = sum(item["price"] * item["quantity"] for item in product_info)
    discount_amount = 0

    # Apply promo code if provided
    promo_code_id = None
    if order_data.promo_code:
        promo_code = await promo_service.get_active_promo_code(order_data.promo_code)
        promo_code_id = promo_code.id
        discount_amount = await promo_service.calculate_discount(promo_code, subtotal)

    total_amount = subtotal - discount_amount

    # Create order
    order = Order(
        user_id=user_id,
        status=OrderStatus.CREATED,
        promo_code_id=promo_code_id,
        total_amount=total_amount,
        discount_amount=discount_amount,
    )
    db.add(order)
    await db.flush()

    # Create order items and reserve stock
    for item_data, product in zip(order_data.items, product_info):
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price_at_order=product["price"],
        )
        db.add(order_item)

        # Reserve stock
        await order_service.reserve_stock(item_data.product_id, item_data.quantity)

    # Record operation
    operation = UserOperation(
        user_id=user_id, operation_type=OperationType.CREATE_ORDER
    )
    db.add(operation)

    await db.commit()
    await db.refresh(order)

    # Build response with product names
    items_response = []
    for item in order.items:
        product = next(
            (p for p in product_info if str(p["id"]) == str(item.product_id)), None
        )
        items_response.append(
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=product["name"] if product else None,
                quantity=item.quantity,
                price_at_order=float(item.price_at_order),
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        items=items_response,
        promo_code_id=order.promo_code_id,
        total_amount=float(order.total_amount),
        discount_amount=float(order.discount_amount),
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Получение заказа по ID"""
    order_service = OrderService(db)

    order = await order_service.get_order(order_id)

    # Check ownership
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ORDER_OWNERSHIP_VIOLATION",
                message="Заказ принадлежит другому пользователю",
            ).model_dump(),
        )

    # Build response
    items_response = []
    for item in order.items:
        items_response.append(
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=None,
                quantity=item.quantity,
                price_at_order=float(item.price_at_order),
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        items=items_response,
        promo_code_id=order.promo_code_id,
        total_amount=float(order.total_amount),
        discount_amount=float(order.discount_amount),
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: uuid.UUID,
    order_data: OrderUpdate,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Обновление заказа"""
    order_service = OrderService(db)
    promo_service = PromoService(db)

    # Rate limiting check
    await order_service.check_rate_limit(user_id, OperationType.UPDATE_ORDER)

    order = await order_service.get_order(order_id)

    # Check ownership
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ORDER_OWNERSHIP_VIOLATION",
                message="Заказ принадлежит другому пользователю",
            ).model_dump(),
        )

    # Check if order can be updated
    if order.status not in [OrderStatus.CREATED, OrderStatus.PAYMENT_PENDING]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error_code="INVALID_STATE_TRANSITION",
                message="Заказ нельзя обновить в текущем статусе",
            ).model_dump(),
        )

    # Validate products and stock
    product_info = await order_service.validate_products(order_data.items)

    # Calculate totals
    subtotal = sum(item["price"] * item["quantity"] for item in product_info)
    discount_amount = 0

    # Apply promo code if exists
    if order.promo_code_id:
        promo_code = await promo_service.get_promo_code_by_id(order.promo_code_id)
        if promo_code:
            discount_amount = await promo_service.calculate_discount(
                promo_code, subtotal
            )

    total_amount = subtotal - discount_amount

    # Restore old stock
    for old_item in order.items:
        await order_service.restore_stock(old_item.product_id, old_item.quantity)

    # Delete old items
    for old_item in order.items:
        await db.delete(old_item)

    # Create new order items and reserve stock
    for item_data, product in zip(order_data.items, product_info):
        order_item = OrderItem(
            order_id=order.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price_at_order=product["price"],
        )
        db.add(order_item)

        # Reserve stock
        await order_service.reserve_stock(item_data.product_id, item_data.quantity)

    # Update order
    order.total_amount = total_amount
    order.discount_amount = discount_amount

    # Record operation
    operation = UserOperation(
        user_id=user_id, operation_type=OperationType.UPDATE_ORDER
    )
    db.add(operation)

    await db.commit()
    await db.refresh(order)

    # Build response
    items_response = []
    for item in order.items:
        product = next(
            (p for p in product_info if str(p["id"]) == str(item.product_id)), None
        )
        items_response.append(
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=product["name"] if product else None,
                quantity=item.quantity,
                price_at_order=float(item.price_at_order),
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        items=items_response,
        promo_code_id=order.promo_code_id,
        total_amount=float(order.total_amount),
        discount_amount=float(order.discount_amount),
        created_at=order.created_at,
        updated_at=order.updated_at,
    )


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: uuid.UUID,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Отмена заказа"""
    order_service = OrderService(db)

    order = await order_service.get_order(order_id)

    # Check ownership
    if order.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                error_code="ORDER_OWNERSHIP_VIOLATION",
                message="Заказ принадлежит другому пользователю",
            ).model_dump(),
        )

    # Check if order can be canceled
    if order.status in [OrderStatus.COMPLETED, OrderStatus.CANCELED]:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error_code="INVALID_STATE_TRANSITION",
                message="Заказ нельзя отменить в текущем статусе",
            ).model_dump(),
        )

    # Restore stock
    for item in order.items:
        await order_service.restore_stock(item.product_id, item.quantity)

    # Update order status
    order.status = OrderStatus.CANCELED

    # Record operation
    operation = UserOperation(
        user_id=user_id, operation_type=OperationType.CANCEL_ORDER
    )
    db.add(operation)

    await db.commit()
    await db.refresh(order)

    # Build response
    items_response = []
    for item in order.items:
        items_response.append(
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=None,
                quantity=item.quantity,
                price_at_order=float(item.price_at_order),
            )
        )

    return OrderResponse(
        id=order.id,
        user_id=order.user_id,
        status=order.status,
        items=items_response,
        promo_code_id=order.promo_code_id,
        total_amount=float(order.total_amount),
        discount_amount=float(order.discount_amount),
        created_at=order.created_at,
        updated_at=order.updated_at,
    )
