from dataclasses import dataclass
from decimal import Decimal

from app.models.order import OrderSide
from app.models.trading import Position, TradingAccount


@dataclass(frozen=True)
class RiskLimits:
    max_order_notional: Decimal = Decimal("100000")
    max_position_notional: Decimal = Decimal("250000")
    max_daily_loss: Decimal = Decimal("25000")
    max_open_orders: int = 20


@dataclass(frozen=True)
class RiskDecision:
    approved: bool
    reasons: tuple[str, ...] = ()


class RiskEngine:
    """Deterministic pre-trade risk checks. This layer must run before execution."""

    def __init__(self, limits: RiskLimits | None = None) -> None:
        self.limits = limits or RiskLimits()

    def evaluate_order(
        self,
        *,
        account: TradingAccount,
        side: OrderSide,
        quantity: Decimal,
        price: Decimal,
        position: Position | None = None,
        open_order_count: int = 0,
    ) -> RiskDecision:
        reasons: list[str] = []
        if quantity <= 0:
            reasons.append("quantity must be greater than zero")
        if price <= 0:
            reasons.append("reference price must be greater than zero")

        if quantity > 0 and price > 0:
            notional = quantity * price
            if notional > self.limits.max_order_notional:
                reasons.append("order notional exceeds configured limit")
            if side == OrderSide.BUY and notional > account.cash_balance:
                reasons.append("insufficient cash balance")
        else:
            notional = Decimal("0")

        if open_order_count >= self.limits.max_open_orders:
            reasons.append("maximum open orders reached")

        existing_qty = position.quantity if position else Decimal("0")
        if side == OrderSide.SELL and quantity > existing_qty:
            reasons.append("sell quantity exceeds available position")
            projected_qty = Decimal("0")
        else:
            projected_qty = existing_qty + quantity if side == OrderSide.BUY else existing_qty - quantity

        projected_notional = abs(projected_qty) * price if price > 0 else Decimal("0")
        if projected_notional > self.limits.max_position_notional:
            reasons.append("projected position notional exceeds configured limit")

        # realized_pnl is the account-level loss proxy until a daily P&L ledger exists.
        if account.realized_pnl <= -self.limits.max_daily_loss:
            reasons.append("daily loss limit has been breached")

        return RiskDecision(approved=not reasons, reasons=tuple(reasons))
