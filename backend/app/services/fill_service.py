from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.fill import Fill
from app.models.order import Order, OrderStatus
from app.models.trading import Position, TradingAccount
from app.services.order_state import validate_transition


class FillService:
    """Apply an execution atomically to order, position, cash, and realized P&L."""

    async def apply_fill(
        self,
        db: AsyncSession,
        *,
        order_id: UUID,
        execution_id: str,
        quantity: Decimal,
        price: Decimal,
        fee: Decimal = Decimal("0"),
        executed_at: datetime | None = None,
    ) -> Fill:
        if not execution_id.strip():
            raise ValueError("execution_id is required")
        if quantity <= 0 or price <= 0 or fee < 0:
            raise ValueError("quantity and price must be positive; fee cannot be negative")

        existing = await db.scalar(select(Fill).where(Fill.execution_id == execution_id))
        if existing:
            if (
                existing.order_id != order_id
                or existing.quantity != quantity
                or existing.price != price
                or existing.fee != fee
            ):
                raise ValueError("execution_id already exists with different execution details")
            return existing

        order = await db.scalar(select(Order).where(Order.id == order_id).with_for_update())
        if order is None:
            raise ValueError("order not found")
        remaining = order.quantity - order.filled_quantity
        if quantity > remaining:
            raise ValueError("fill quantity exceeds remaining order quantity")

        new_filled = order.filled_quantity + quantity
        target_status = OrderStatus.FILLED if new_filled == order.quantity else OrderStatus.PARTIALLY_FILLED
        validate_transition(order.status, target_status)

        account = await db.scalar(select(TradingAccount).where(TradingAccount.id == order.account_id).with_for_update())
        if account is None:
            raise ValueError("trading account not found")

        symbol = order.symbol.upper()
        position = await db.scalar(
            select(Position).where(Position.account_id == account.id, Position.symbol == symbol).with_for_update()
        )
        if position is None:
            position = Position(account_id=account.id, symbol=symbol)
            db.add(position)
            await db.flush()

        old_qty = position.quantity
        old_avg = position.average_price
        signed_qty = quantity if order.side.value == "BUY" else -quantity
        new_qty = old_qty + signed_qty

        if old_qty == 0 or (old_qty > 0 and signed_qty > 0) or (old_qty < 0 and signed_qty < 0):
            position.average_price = (abs(old_qty) * old_avg + quantity * price) / abs(new_qty)
        elif new_qty == 0:
            position.average_price = Decimal("0")
        else:
            closed_qty = min(abs(old_qty), quantity)
            if old_qty > 0:
                account.realized_pnl += (price - old_avg) * closed_qty
            else:
                account.realized_pnl += (old_avg - price) * closed_qty
            if old_qty * new_qty < 0:
                position.average_price = price

        position.quantity = new_qty
        position.market_price = price
        position.unrealized_pnl = (price - position.average_price) * new_qty

        cash_delta = -signed_qty * price - fee
        account.cash_balance += cash_delta

        fill = Fill(
            order_id=order.id,
            account_id=account.id,
            execution_id=execution_id,
            symbol=symbol,
            quantity=quantity,
            price=price,
            fee=fee,
            executed_at=executed_at or datetime.now(timezone.utc),
        )
        db.add(fill)
        order.filled_quantity = new_filled
        order.average_fill_price = (
            ((order.average_fill_price or Decimal("0")) * (new_filled - quantity) + price * quantity) / new_filled
        )
        order.status = target_status
        await db.commit()
        await db.refresh(fill)
        return fill
