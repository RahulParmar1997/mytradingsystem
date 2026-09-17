"""add fill persistence

Revision ID: 0005_fills
Revises: 0004_risk_limits
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0005_fills"
down_revision = "0004_risk_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "fills",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("order_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trading_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("execution_id", sa.String(128), nullable=False, unique=True),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("price", sa.Numeric(20, 8), nullable=False),
        sa.Column("fee", sa.Numeric(20, 8), nullable=False, server_default="0"),
        sa.Column("executed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_fills_order_id", "fills", ["order_id"])
    op.create_index("ix_fills_account_id", "fills", ["account_id"])
    op.create_index("ix_fills_order_created", "fills", ["order_id", "created_at"])
    op.create_index("ix_fills_account_created", "fills", ["account_id", "created_at"])
    op.create_index("ix_fills_symbol", "fills", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_fills_symbol", table_name="fills")
    op.drop_index("ix_fills_account_created", table_name="fills")
    op.drop_index("ix_fills_order_created", table_name="fills")
    op.drop_index("ix_fills_account_id", table_name="fills")
    op.drop_index("ix_fills_order_id", table_name="fills")
    op.drop_table("fills")
