"""Product service business logic."""

import uuid
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import Product, ProductStatus


class ProductService:
    """Service for product business logic."""

    @staticmethod
    async def create_product(
        session: AsyncSession,
        name: str,
        description: str | None,
        price: float,
        stock: int,
        category: str,
        status: ProductStatus,
        seller_id: uuid.UUID,
    ) -> Product:
        """Create a new product."""
        product = Product(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category=category,
            status=status,
            seller_id=seller_id,
        )
        session.add(product)
        await session.flush()
        await session.refresh(product)
        return product

    @staticmethod
    async def get_product(
        session: AsyncSession,
        product_id: uuid.UUID,
    ) -> Product | None:
        """Get a product by ID."""
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_products(
        session: AsyncSession,
        page: int = 0,
        size: int = 20,
        status: ProductStatus | None = None,
        category: str | None = None,
    ) -> tuple[list[Product], int]:
        """List products with pagination and filtering."""
        query: Select[tuple[Product]] = select(Product)

        # Apply filters
        if status is not None:
            query = query.where(Product.status == status)
        if category is not None:
            query = query.where(Product.category == category)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await session.execute(count_query)
        total = total_result.scalar()

        # Apply pagination
        query = query.offset(page * size).limit(size)
        result = await session.execute(query)
        products = list(result.scalars().all())

        return products, total

    @staticmethod
    async def update_product(
        session: AsyncSession,
        product_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        price: float | None = None,
        stock: int | None = None,
        category: str | None = None,
        status: ProductStatus | None = None,
    ) -> Product | None:
        """Update a product."""
        product = await ProductService.get_product(session, product_id)
        if product is None:
            return None

        update_data: dict[str, Any] = {}
        if name is not None:
            update_data["name"] = name
        if description is not None:
            update_data["description"] = description
        if price is not None:
            update_data["price"] = price
        if stock is not None:
            update_data["stock"] = stock
        if category is not None:
            update_data["category"] = category
        if status is not None:
            update_data["status"] = status

        for key, value in update_data.items():
            setattr(product, key, value)

        await session.flush()
        await session.refresh(product)
        return product

    @staticmethod
    async def delete_product(
        session: AsyncSession,
        product_id: uuid.UUID,
    ) -> bool:
        """Soft delete a product by setting status to ARCHIVED."""
        product = await ProductService.get_product(session, product_id)
        if product is None:
            return False

        product.status = ProductStatus.ARCHIVED
        await session.flush()
        return True
