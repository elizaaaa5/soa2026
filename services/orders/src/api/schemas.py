from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime
from enum import Enum
import uuid
import re


class OrderStatus(str, Enum):
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class DiscountType(str, Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(ge=1, le=999)

    @field_validator("quantity")
    @classmethod
    def validate_quantity(cls, v):
        if v < 1 or v > 999:
            raise ValueError("Quantity must be between 1 and 999")
        return v


class OrderCreate(BaseModel):
    items: List[OrderItemCreate] = Field(min_length=1, max_length=50)
    promo_code: Optional[str] = Field(None, pattern=r"^[A-Z0-9_]{4,20}$")

    @field_validator("promo_code")
    @classmethod
    def validate_promo_code(cls, v):
        if v and not re.match(r"^[A-Z0-9_]{4,20}$", v):
            raise ValueError("Promo code must be 4-20 characters (A-Z, 0-9, _)")
        return v


class OrderUpdate(BaseModel):
    items: List[OrderItemCreate] = Field(min_length=1, max_length=50)


class OrderItemResponse(BaseModel):
    id: uuid.UUID
    product_id: uuid.UUID
    product_name: Optional[str] = None
    quantity: int
    price_at_order: float


class OrderResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: OrderStatus
    items: List[OrderItemResponse]
    promo_code_id: Optional[uuid.UUID] = None
    total_amount: float
    discount_amount: float
    created_at: datetime
    updated_at: Optional[datetime] = None


class PromoCodeCreate(BaseModel):
    code: str = Field(pattern=r"^[A-Z0-9_]{4,20}$")
    discount_type: DiscountType
    discount_value: float = Field(ge=0.01)
    min_order_amount: float = Field(ge=0, default=0)
    max_uses: int = Field(ge=1)
    valid_from: datetime
    valid_until: datetime

    @field_validator("code")
    @classmethod
    def validate_code(cls, v):
        if not re.match(r"^[A-Z0-9_]{4,20}$", v):
            raise ValueError("Code must be 4-20 characters (A-Z, 0-9, _)")
        return v


class PromoCodeResponse(BaseModel):
    id: uuid.UUID
    code: str
    discount_type: DiscountType
    discount_value: float
    min_order_amount: float
    max_uses: int
    current_uses: int
    valid_from: datetime
    valid_until: datetime
    active: bool


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
