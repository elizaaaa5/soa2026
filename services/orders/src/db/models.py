from sqlalchemy import (
    Column,
    String,
    Integer,
    Numeric,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from src.db.session import Base


class OrderStatus(str, enum.Enum):
    CREATED = "CREATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    COMPLETED = "COMPLETED"
    CANCELED = "CANCELED"


class DiscountType(str, enum.Enum):
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class OperationType(str, enum.Enum):
    CREATE_ORDER = "CREATE_ORDER"
    UPDATE_ORDER = "UPDATE_ORDER"
    CANCEL_ORDER = "CANCEL_ORDER"


class Order(Base):
    __tablename__ = "orders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    status = Column(SQLEnum(OrderStatus), nullable=False, default=OrderStatus.CREATED)
    promo_code_id = Column(
        UUID(as_uuid=True), ForeignKey("promo_codes.id"), nullable=True
    )
    total_amount = Column(Numeric(10, 2), nullable=False)
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    items = relationship(
        "OrderItem", back_populates="order", cascade="all, delete-orphan"
    )
    promo_code = relationship("PromoCode", back_populates="orders")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    order_id = Column(UUID(as_uuid=True), ForeignKey("orders.id"), nullable=False)
    product_id = Column(UUID(as_uuid=True), nullable=False)
    quantity = Column(Integer, nullable=False)
    price_at_order = Column(Numeric(10, 2), nullable=False)

    order = relationship("Order", back_populates="items")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    code = Column(String(20), nullable=False, unique=True, index=True)
    discount_type = Column(SQLEnum(DiscountType), nullable=False)
    discount_value = Column(Numeric(10, 2), nullable=False)
    min_order_amount = Column(Numeric(10, 2), nullable=False, default=0)
    max_uses = Column(Integer, nullable=False)
    current_uses = Column(Integer, nullable=False, default=0)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=False)
    active = Column(Boolean, nullable=False, default=True)

    orders = relationship("Order", back_populates="promo_code")


class UserOperation(Base):
    __tablename__ = "user_operations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    operation_type = Column(SQLEnum(OperationType), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
