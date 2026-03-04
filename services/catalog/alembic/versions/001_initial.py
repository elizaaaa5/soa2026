"""Initial migration for products table."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database."""
    # Check if type exists before creating
    conn = op.get_bind()
    if not conn.dialect.has_type(conn, "product_status"):
        op.execute(
            "CREATE TYPE product_status AS ENUM ('ACTIVE', 'INACTIVE', 'ARCHIVED')"
        )

    # Define enum for use in create_table (without creating)
    product_status_enum = postgresql.ENUM(
        "ACTIVE", "INACTIVE", "ARCHIVED", name="product_status", create_type=False
    )

    # Create products table
    op.create_table(
        "products",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
        ),
        sa.Column(
            "name",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "price",
            sa.Numeric(10, 2),
            nullable=False,
        ),
        sa.Column(
            "stock",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "category",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "status",
            product_status_enum,
            nullable=False,
            server_default="ACTIVE",
        ),
        sa.Column(
            "seller_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # Create index on status
    op.create_index(
        "ix_products_status",
        "products",
        ["status"],
    )


def downgrade() -> None:
    """Downgrade database."""
    # Drop index
    op.drop_index("ix_products_status", table_name="products")

    # Drop table
    op.drop_table("products")

    # Drop enum type
    product_status_enum = postgresql.ENUM(
        "ACTIVE", "INACTIVE", "ARCHIVED", name="product_status", create_type=False
    )
    product_status_enum.drop(op.get_bind())
