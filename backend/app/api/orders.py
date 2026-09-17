from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.order import Order, OrderStatus
from app.models.trading import TradingAccount
from app.models.user import User
from app.schemas.orders import OrderCreate, OrderResponse

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Order:
    account = await db.scalar(
        select(TradingAccount).where(TradingAccount.id == payload.account_id, TradingAccount.user_id == user.id)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Trading account not found")

    existing = await db.scalar(select(Order).where(Order.client_order_id == payload.client_order_id))
    if existing:
        if existing.account_id != account.id:
            raise HTTPException(status_code=409, detail="Client order id already exists")
        return existing

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
        status=OrderStatus.PENDING,
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
