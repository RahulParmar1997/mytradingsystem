from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.order import Order, OrderStatus, OrderType
from app.models.risk import RiskLimit
from app.models.trading import Position, TradingAccount
from app.models.user import User
from app.risk.engine import RiskEngine, RiskLimits
from app.schemas.orders import OrderCreate, OrderResponse

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])
OPEN_STATUSES = ["PENDING", "ACCEPTED", "PARTIALLY_FILLED", "CANCEL_PENDING"]


def build_engine(limits: RiskLimit | None) -> RiskEngine:
    if limits is None:
        return RiskEngine()
    return RiskEngine(
        RiskLimits(
            max_order_notional=limits.max_order_notional,
            max_position_notional=limits.max_position_notional,
            max_daily_loss=limits.max_daily_loss,
            max_open_orders=limits.max_open_orders,
        )
    )


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Order:
    account = await db.scalar(
        select(TradingAccount)
        .where(TradingAccount.id == payload.account_id, TradingAccount.user_id == user.id)
        .with_for_update()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Trading account not found")

    existing = await db.scalar(select(Order).where(Order.client_order_id == payload.client_order_id))
    if existing:
        if existing.account_id != account.id:
            raise HTTPException(status_code=409, detail="Client order id already exists")
        return existing

    if payload.order_type == OrderType.MARKET:
        risk_reason = "market orders require a market-data reference price"
        order = Order(
            account_id=account.id,
            client_order_id=payload.client_order_id,
            symbol=payload.symbol.upper(),
            side=payload.side,
            order_type=payload.order_type,
            time_in_force=payload.time_in_force,
            quantity=payload.quantity,
            limit_price=payload.limit_price,
            stop_price=payload.stop_price,
            status=OrderStatus.REJECTED,
            rejection_reason=risk_reason,
        )
        db.add(order)
        await db.commit()
        await db.refresh(order)
        return order

    reference_price = payload.limit_price or payload.stop_price
    position = await db.scalar(
        select(Position).where(Position.account_id == account.id, Position.symbol == payload.symbol.upper())
    )
    open_order_count = await db.scalar(
        select(func.count(Order.id)).where(
            Order.account_id == account.id,
            Order.status.in_(OPEN_STATUSES),
        )
    )
    limits = await db.scalar(select(RiskLimit).where(RiskLimit.account_id == account.id))
    decision = build_engine(limits).evaluate_order(
        account=account,
        side=payload.side,
        quantity=payload.quantity,
        price=reference_price or 0,
        position=position,
        open_order_count=int(open_order_count or 0),
    )

    order = Order(
        account_id=account.id,
        client_order_id=payload.client_order_id,
        symbol=payload.symbol.upper(),
        side=payload.side,
        order_type=payload.order_type,
        time_in_force=payload.time_in_force,
        quantity=payload.quantity,
        limit_price=payload.limit_price,
        stop_price=payload.stop_price,
        status=OrderStatus.PENDING if decision.approved else OrderStatus.REJECTED,
        rejection_reason=None if decision.approved else "; ".join(decision.reasons),
    )
    db.add(order)
    await db.commit()
    await db.refresh(order)
    return order


@router.get("", response_model=list[OrderResponse])
async def list_orders(
    account_id: UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Order]:
    query = (
        select(Order)
        .join(TradingAccount, TradingAccount.id == Order.account_id)
        .where(TradingAccount.user_id == user.id)
        .order_by(Order.created_at.desc())
    )
    if account_id:
        query = query.where(Order.account_id == account_id)
    result = await db.scalars(query)
    return list(result.all())


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Order:
    order = await db.scalar(
        select(Order).join(TradingAccount, TradingAccount.id == Order.account_id).where(
            Order.id == order_id, TradingAccount.user_id == user.id
        )
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
