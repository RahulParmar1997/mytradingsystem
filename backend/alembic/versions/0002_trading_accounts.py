"""add trading accounts and positions

Revision ID: 0002_trading_accounts
Revises: 0001_auth_persistence
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0002_trading_accounts"
down_revision = "0001_auth_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "trading_accounts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False),
        sa.Column("initial_balance", sa.Numeric(20, 8), nullable=False),
        sa.Column("cash_balance", sa.Numeric(20, 8), nullable=False),
        sa.Column("realized_pnl", sa.Numeric(20, 8), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_trading_accounts_user_id", "trading_accounts", ["user_id"])

    op.create_table(
        "positions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("account_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("trading_accounts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("symbol", sa.String(32), nullable=False),
        sa.Column("quantity", sa.Numeric(20, 8), nullable=False),
        sa.Column("average_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("market_price", sa.Numeric(20, 8), nullable=False),
        sa.Column("unrealized_pnl", sa.Numeric(20, 8), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("account_id", "symbol", name="uq_positions_account_symbol"),
    )
    op.create_index("ix_positions_account_id", "positions", ["account_id"])
    op.create_index("ix_positions_symbol", "positions", ["symbol"])


def downgrade() -> None:
    op.drop_index("ix_positions_symbol", table_name="positions")
    op.drop_index("ix_positions_account_id", table_name="positions")
    op.drop_table("positions")
    op.drop_index("ix_trading_accounts_user_id", table_name="trading_accounts")
    op.drop_table("trading_accounts")
