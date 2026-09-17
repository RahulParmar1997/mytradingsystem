from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.services.fill_service import FillService
from app.services.order_state import validate_transition


@dataclass(frozen=True)
class ExecutionResult:
    status: OrderStatus
    filled_quantity: Decimal
    fill_id: UUID | None = None


class ExecutionEngine:
    """Routes approved orders to an execution adapter and keeps OMS state consistent."""

    def __init__(self, broker, fill_service: FillService | None = None) -> None:
        self.broker = broker
        self.fill_service = fill_service or FillService()

    async def execute_order(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        execution_id: str,
        price: Decimal,
        quantity: Decimal | None = None,
        fee: Decimal = Decimal("0"),
    ) -> ExecutionResult:
        order = await db.scalar(select(Order).where(Order.id == order_id).with_for_update())
        if order is None:
            raise ValueError("order not found")
        if order.status not in {OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}:
            raise ValueError(f"order cannot be executed from status {order.status.value}")

        remaining = order.quantity - order.filled_quantity
        execution_quantity = quantity if quantity is not None else remaining
        if execution_quantity <= 0:
            raise ValueError("execution quantity must be positive")
        if execution_quantity > remaining:
            raise ValueError("execution quantity exceeds remaining order quantity")

        if order.status == OrderStatus.PENDING:
            validate_transition(order.status, OrderStatus.ACCEPTED)
            order.status = OrderStatus.ACCEPTED
            await db.flush()

        result = await self.broker.execute(
            db,
            order_id=order_id,
            execution_id=execution_id,
            quantity=execution_quantity,
            price=price,
            fee=fee,
        )
        return ExecutionResult(
            status=result and (await db.scalar(select(Order.status).where(Order.id == order_id))) or order.status,
            filled_quantity=execution_quantity,
            fill_id=result.id if result else None,
        )
