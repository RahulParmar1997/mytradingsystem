"""add persistent account risk limits

Revision ID: 0004_risk_limits
Revises: 0003_orders
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0004_risk_limits"
down_revision = "0003_orders"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "risk_limits",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "account_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("trading_accounts.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("max_order_notional", sa.Numeric(20, 8), nullable=False, server_default="100000"),
        sa.Column("max_position_notional", sa.Numeric(20, 8), nullable=False, server_default="250000"),
        sa.Column("max_daily_loss", sa.Numeric(20, 8), nullable=False, server_default="25000"),
        sa.Column("max_open_orders", sa.Integer(), nullable=False, server_default="20"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_limits_account_id", "risk_limits", ["account_id"], unique=True)

    op.execute(
        """
        INSERT INTO risk_limits (id, account_id, max_order_notional, max_position_notional, max_daily_loss, max_open_orders, created_at, updated_at)
        SELECT gen_random_uuid(), id, 100000, 250000, 25000, 20, NOW(), NOW()
        FROM trading_accounts
        """
    )


def downgrade() -> None:
    op.drop_index("ix_risk_limits_account_id", table_name="risk_limits")
    op.drop_table("risk_limits")
