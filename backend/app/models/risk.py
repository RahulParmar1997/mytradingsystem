from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class RiskLimit(Base):
    __tablename__ = "risk_limits"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    account_id: Mapped[UUID] = mapped_column(
        ForeignKey("trading_accounts.id", ondelete="CASCADE"), nullable=False, unique=True, index=True
    )
    max_order_notional: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=Decimal("100000"))
    max_position_notional: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=Decimal("250000"))
    max_daily_loss: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False, default=Decimal("25000"))
    max_open_orders: Mapped[int] = mapped_column(Integer, nullable=False, default=20)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False
    )
