from decimal import Decimal

from app.models.order import OrderSide
from app.models.trading import Position, TradingAccount
from app.risk.engine import RiskEngine, RiskLimits


def make_account() -> TradingAccount:
    return TradingAccount(
        initial_balance=Decimal("100000"),
        cash_balance=Decimal("100000"),
        realized_pnl=Decimal("0"),
    )


def test_approves_order_within_limits() -> None:
    decision = RiskEngine().evaluate_order(
        account=make_account(),
        side=OrderSide.BUY,
        quantity=Decimal("10"),
        price=Decimal("100"),
    )

    assert decision.approved
    assert decision.reasons == ()


def test_rejects_order_notional_above_limit() -> None:
    decision = RiskEngine(RiskLimits(max_order_notional=Decimal("1000"))).evaluate_order(
        account=make_account(),
        side=OrderSide.BUY,
        quantity=Decimal("11"),
        price=Decimal("100"),
    )

    assert not decision.approved
    assert "order notional exceeds configured limit" in decision.reasons


def test_rejects_sell_above_position() -> None:
    position = Position(quantity=Decimal("5"))
    decision = RiskEngine().evaluate_order(
        account=make_account(),
        side=OrderSide.SELL,
        quantity=Decimal("6"),
        price=Decimal("100"),
        position=position,
    )

    assert not decision.approved
    assert "sell quantity exceeds available position" in decision.reasons


def test_rejects_when_daily_loss_limit_is_reached() -> None:
    account = make_account()
    account.realized_pnl = Decimal("-25000")

    decision = RiskEngine().evaluate_order(
        account=account,
        side=OrderSide.BUY,
        quantity=Decimal("1"),
        price=Decimal("100"),
    )

    assert not decision.approved
    assert "daily loss limit has been breached" in decision.reasons
