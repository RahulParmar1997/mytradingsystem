from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.order import Order, OrderStatus
from app.services.order_state import validate_transition


@dataclass(frozen=True)
class CancelResult:
    order_id: UUID
    status: OrderStatus


class CancelEngine:
    """Coordinates order cancellation without fabricating broker-side fills."""

    async def request_cancel(self, db: AsyncSession, *, order_id: UUID) -> CancelResult:
        order = await db.scalar(select(Order).where(Order.id == order_id).with_for_update())
        if order is None:
            raise ValueError("order not found")

        if order.status in {OrderStatus.PENDING, OrderStatus.ACCEPTED, OrderStatus.PARTIALLY_FILLED}:
            validate_transition(order.status, OrderStatus.CANCEL_PENDING)
            order.status = OrderStatus.CANCEL_PENDING
            await db.commit()
            return CancelResult(order.id, order.status)

        if order.status == OrderStatus.CANCEL_PENDING:
            return CancelResult(order.id, order.status)

        raise ValueError(f"order cannot be cancelled from status {order.status.value}")

    async def confirm_cancel(self, db: AsyncSession, *, order_id: UUID) -> CancelResult:
        order = await db.scalar(select(Order).where(Order.id == order_id).with_for_update())
        if order is None:
            raise ValueError("order not found")
        validate_transition(order.status, OrderStatus.CANCELLED)
        order.status = OrderStatus.CANCELLED
        await db.commit()
        return CancelResult(order.id, order.status)
