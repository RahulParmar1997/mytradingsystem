from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.fill_service import FillService


@dataclass(frozen=True)
class PaperExecution:
    order_id: UUID
    execution_id: str
    quantity: Decimal
    price: Decimal
    fee: Decimal = Decimal("0")
    executed_at: datetime | None = None


class PaperBroker:
    """Deterministic paper broker: accepts an execution instruction and records a fill."""

    def __init__(self, fill_service: FillService | None = None) -> None:
        self.fill_service = fill_service or FillService()

    async def execute(self, db: AsyncSession, execution: PaperExecution):
        return await self.fill_service.apply_fill(
            db,
            order_id=execution.order_id,
            execution_id=execution.execution_id,
            quantity=execution.quantity,
            price=execution.price,
            fee=execution.fee,
            executed_at=execution.executed_at,
        )
