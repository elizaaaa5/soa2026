"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-03-04 19:30:00.000000

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()

    # Create ENUM types if they don't exist
    for enum_name, enum_values in [
        (
            "orderstatus",
            ["CREATED", "PAYMENT_PENDING", "PAID", "SHIPPED", "COMPLETED", "CANCELED"],
        ),
        ("discounttype", ["PERCENTAGE", "FIXED_AMOUNT"]),
        ("operationtype", ["CREATE_ORDER", "UPDATE_ORDER", "CANCEL_ORDER"]),
    ]:
        if not conn.dialect.has_type(conn, enum_name):
            op.execute(f"CREATE TYPE {enum_name} AS ENUM {tuple(enum_values)}")

    # Create promo_codes table first (no dependencies)
    op.create_table(
        "promo_codes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("code", sa.String(20), nullable=False),
        sa.Column(
            "discount_type",
            sa.Enum("PERCENTAGE", "FIXED_AMOUNT", name="discounttype"),
            nullable=False,
        ),
        sa.Column("discount_value", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "min_order_amount", sa.Numeric(10, 2), nullable=False, server_default="0"
        ),
        sa.Column("max_uses", sa.Integer(), nullable=False),
        sa.Column("current_uses", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("valid_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("valid_until", sa.DateTime(timezone=True), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default="true"),
    )
    op.create_index(op.f("ix_promo_codes_code"), "promo_codes", ["code"], unique=True)

    # Create order_items table (depends on orders, but orders depends on promo_codes)
    op.create_table(
        "order_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("price_at_order", sa.Numeric(10, 2), nullable=False),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"]),
    )

    # Create orders table (depends on promo_codes)
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "CREATED",
                "PAYMENT_PENDING",
                "PAID",
                "SHIPPED",
                "COMPLETED",
                "CANCELED",
                name="orderstatus",
            ),
            nullable=False,
        ),
        sa.Column("promo_code_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("total_amount", sa.Numeric(10, 2), nullable=False),
        sa.Column(
            "discount_amount", sa.Numeric(10, 2), nullable=False, server_default="0"
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True)),
        sa.ForeignKeyConstraint(["promo_code_id"], ["promo_codes.id"]),
    )
    op.create_index(op.f("ix_orders_user_id"), "orders", ["user_id"])

    # Create user_operations table (no dependencies)
    op.create_table(
        "user_operations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "operation_type",
            sa.Enum(
                "CREATE_ORDER", "UPDATE_ORDER", "CANCEL_ORDER", name="operationtype"
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")
        ),
    )
    op.create_index(op.f("ix_user_operations_user_id"), "user_operations", ["user_id"])


def downgrade() -> None:
    op.drop_index(op.f("ix_user_operations_user_id"), table_name="user_operations")
    op.drop_table("user_operations")

    op.drop_index(op.f("ix_orders_user_id"), table_name="orders")
    op.drop_table("orders")

    op.drop_table("order_items")

    op.drop_index(op.f("ix_promo_codes_code"), table_name="promo_codes")
    op.drop_table("promo_codes")
