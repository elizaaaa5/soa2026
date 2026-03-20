"""API schemas for Catalog Service."""

from pydantic import BaseModel, Field


class ErrorResponse(BaseModel):
    """Schema for error response."""

    error_code: str
    message: str
    details: dict | None = None


# Old schemas - replaced by generated models from OpenAPI spec
# See: src.api.generated.models
#
# class ProductStatus(str, Enum):
#     """Product status enum."""
#     ACTIVE = "ACTIVE"
#     INACTIVE = "INACTIVE"
#     ARCHIVED = "ARCHIVED"
#
# class ProductCreate(BaseModel):
#     """Schema for creating a product."""
#     ...
#
# class ProductUpdate(BaseModel):
#     """Schema for updating a product."""
#     ...
#
# class ProductResponse(BaseModel):
#     """Schema for product response."""
#     ...
#
# class ProductListResponse(BaseModel):
#     """Schema for product list response."""
#     ...
