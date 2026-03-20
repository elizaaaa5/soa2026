"""Product API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Annotated

from src.api.generated.models import (
    ErrorResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from src.api.deps import get_current_user, require_role
from src.db.models import Product, ProductStatus
from src.db.session import get_session
from src.services.product_service import ProductService
from pydantic import BaseModel


class StockRequest(BaseModel):
    quantity: int


router = APIRouter(prefix="/products", tags=["products"])


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
    },
)
async def create_product(
    product_data: ProductCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[dict, Depends(require_role("SELLER", "ADMIN"))],
) -> ProductResponse:
    """Create a new product."""
    # Convert generated ProductStatus to db ProductStatus
    status_mapping = {
        "ACTIVE": ProductStatus.ACTIVE,
        "INACTIVE": ProductStatus.INACTIVE,
        "ARCHIVED": ProductStatus.ARCHIVED,
    }
    db_status = status_mapping.get(product_data.status.value, ProductStatus.ACTIVE)

    product = await ProductService.create_product(
        session=session,
        name=product_data.name,
        description=product_data.description,
        price=float(product_data.price),
        stock=product_data.stock,
        category=product_data.category,
        status=db_status,
        seller_id=uuid.UUID(current_user["id"]),
    )
    return ProductResponse.model_validate(product)


@router.get(
    "",
    response_model=ProductListResponse,
)
async def list_products(
    session: Annotated[AsyncSession, Depends(get_session)],
    page: Annotated[int, Query(ge=0)] = 0,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    status_filter: Annotated[ProductStatus | None, Query(alias="status")] = None,
    category: Annotated[str | None, Query(max_length=100)] = None,
) -> ProductListResponse:
    """List products with pagination and filtering."""
    products, total = await ProductService.list_products(
        session=session,
        page=page,
        size=size,
        status=status_filter,
        category=category,
    )
    return ProductListResponse(
        content=[ProductResponse.model_validate(p) for p in products],
        total_elements=total,
        page=page,
        size=size,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    responses={
        404: {"model": ErrorResponse},
    },
)
async def get_product(
    product_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> ProductResponse:
    """Get a product by ID."""
    product = await ProductService.get_product(session=session, product_id=product_id)
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PRODUCT_NOT_FOUND",
                "message": "Product not found",
            },
        )
    return ProductResponse.model_validate(product)


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def update_product(
    product_id: uuid.UUID,
    product_data: ProductUpdate,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[dict, Depends(require_role("SELLER", "ADMIN"))],
) -> ProductResponse:
    """Update a product."""
    # Get the product first to check ownership
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PRODUCT_NOT_FOUND",
                "message": "Product not found",
            },
        )

    # Check if user is SELLER and owns the product
    if current_user["role"] == "SELLER" and product.seller_id != uuid.UUID(
        current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ACCESS_DENIED",
                "message": "You can only update your own products",
            },
        )

    # Convert generated ProductStatus to db ProductStatus if provided
    status_mapping = {
        "ACTIVE": ProductStatus.ACTIVE,
        "INACTIVE": ProductStatus.INACTIVE,
        "ARCHIVED": ProductStatus.ARCHIVED,
    }
    db_status = None
    if product_data.status:
        db_status = status_mapping.get(product_data.status.value)

    product = await ProductService.update_product(
        session=session,
        product_id=product_id,
        name=product_data.name,
        description=product_data.description,
        price=float(product_data.price) if product_data.price else None,
        stock=product_data.stock,
        category=product_data.category,
        status=db_status,
    )
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PRODUCT_NOT_FOUND",
                "message": "Product not found",
            },
        )
    return ProductResponse.model_validate(product)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def delete_product(
    product_id: uuid.UUID,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[dict, Depends(require_role("SELLER", "ADMIN"))],
) -> None:
    """Soft delete a product (set status to ARCHIVED)."""
    # Get the product first to check ownership
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PRODUCT_NOT_FOUND",
                "message": "Product not found",
            },
        )

    # Check if user is SELLER and owns the product
    if current_user["role"] == "SELLER" and product.seller_id != uuid.UUID(
        current_user["id"]
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "ACCESS_DENIED",
                "message": "You can only delete your own products",
            },
        )

    success = await ProductService.delete_product(
        session=session, product_id=product_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PRODUCT_NOT_FOUND",
                "message": "Product not found",
            },
        )


@router.post(
    "/batch",
    response_model=list[ProductResponse],
    responses={
        400: {"model": ErrorResponse},
    },
)
async def get_products_batch(
    product_ids: list[str],
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[ProductResponse]:
    """Get multiple products by IDs in a single request."""
    # Convert string IDs to UUIDs
    try:
        uuids = [uuid.UUID(pid) for pid in product_ids]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_PRODUCT_ID",
                "message": "Invalid product ID format",
            },
        )

    # Query products
    result = await session.execute(select(Product).where(Product.id.in_(uuids)))
    products = list(result.scalars().all())

    # Return as ProductResponse
    return [ProductResponse.model_validate(p) for p in products]


@router.post("/{product_id}/reserve")
async def reserve_stock(
    product_id: uuid.UUID,
    request: StockRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Резервирование товара на складе."""
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PRODUCT_NOT_FOUND",
                "message": "Product not found",
            },
        )

    if product.stock < request.quantity:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "error_code": "INSUFFICIENT_STOCK",
                "message": "Insufficient stock",
            },
        )

    product.stock -= request.quantity
    await session.commit()

    return {"success": True, "remaining_stock": product.stock}


@router.post("/{product_id}/restore")
async def restore_stock(
    product_id: uuid.UUID,
    request: StockRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> dict:
    """Восстановление товара на складе."""
    result = await session.execute(select(Product).where(Product.id == product_id))
    product = result.scalar_one_or_none()

    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error_code": "PRODUCT_NOT_FOUND",
                "message": "Product not found",
            },
        )

    product.stock += request.quantity
    await session.commit()

    return {"success": True, "remaining_stock": product.stock}
