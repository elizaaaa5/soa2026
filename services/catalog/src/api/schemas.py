"""API schemas for Catalog Service."""

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ProductStatus(str, Enum):
    """Product status enum."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class ProductCreate(BaseModel):
    """Schema for creating a product."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(None, max_length=4000)
    price: float = Field(..., gt=0)
    stock: int = Field(..., ge=0)
    category: str = Field(..., min_length=1, max_length=100)
    status: ProductStatus = ProductStatus.ACTIVE

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name length."""
        if not (1 <= len(v) <= 255):
            raise ValueError("name must be between 1 and 255 characters")
        return v


class ProductUpdate(BaseModel):
    """Schema for updating a product."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=4000)
    price: float | None = Field(None, gt=0)
    stock: int | None = Field(None, ge=0)
    category: str | None = Field(None, min_length=1, max_length=100)
    status: ProductStatus | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str | None) -> str | None:
        """Validate name length."""
        if v is not None and not (1 <= len(v) <= 255):
            raise ValueError("name must be between 1 and 255 characters")
        return v


class ProductResponse(BaseModel):
    """Schema for product response."""

    id: uuid.UUID
    name: str
    description: str | None
    price: float
    stock: int
    category: str
    status: ProductStatus
    seller_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    """Schema for product list response."""

    content: list[ProductResponse]
    total_elements: int
    page: int
    size: int


class ErrorResponse(BaseModel):
    """Schema for error response."""

    error_code: str
    message: str
    details: dict | None = None
