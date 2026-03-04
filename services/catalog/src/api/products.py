"""Product API endpoints."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.schemas import (
    ErrorResponse,
    ProductCreate,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from src.db.models import Product, ProductStatus
from src.db.session import get_session
from src.services.product_service import ProductService

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
    seller_id: Annotated[uuid.UUID, Query(..., description="Seller ID")],
) -> ProductResponse:
    """Create a new product."""
    product = await ProductService.create_product(
        session=session,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock,
        category=product_data.category,
        status=product_data.status,
        seller_id=seller_id,
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
) -> ProductResponse:
    """Update a product."""
    product = await ProductService.update_product(
        session=session,
        product_id=product_id,
        name=product_data.name,
        description=product_data.description,
        price=product_data.price,
        stock=product_data.stock,
        category=product_data.category,
        status=product_data.status,
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
) -> None:
    """Soft delete a product (set status to ARCHIVED)."""
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
