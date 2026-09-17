"""add order management

Revision ID: 0003_orders
Revises: 0002_trading_accounts
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0003_orders"
down_revision = "0002_trading_accounts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trading_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("client_order_id", sa.String(64), nullable=False, unique=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("side", sa.String(8), nullable=False),
        sa.Column("order_type", sa.String(16), nullable=False),
        sa.Column("time_in_force", sa.String(8), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("limit_price", sa.Numeric(20, 8)),
        sa.Column("stop_price", sa.Numeric(20, 8)),
        sa.Column("filled_quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("average_fill_price", sa.Numeric(20, 8)),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("rejection_reason", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_orders_account_id", "orders", ["account_id"])
    op.create_index("ix_orders_symbol", "orders", ["symbol"])
    op.create_index("ix_orders_account_created", "orders", ["account_id", "created_at"])
    op.create_index("ix_orders_account_status", "orders", ["account_id", "status"])


def downgrade() -> None:
    op.drop_index("ix_orders_account_status", table_name="orders")
    op.drop_index("ix_orders_account_created", table_name="orders")
    op.drop_index("ix_orders_symbol", table_name="orders")
    op.drop_index("ix_orders_account_id", table_name="orders")
    op.drop_table("orders")
