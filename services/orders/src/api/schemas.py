from pydantic import BaseModel
from typing import Optional, Any


# Old manual DTOs - replaced by generated models in src.api.generated.models
# Kept only ErrorResponse for error handling
# class OrderStatus, DiscountType, OrderCreate, OrderUpdate, OrderResponse, OrderItemResponse, PromoCodeCreate, PromoCodeResponse
# are now imported from src.api.generated.models


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[dict] = None
