from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.order import Order
from app.models.trading import TradingAccount
from app.models.user import User
from app.schemas.cancel import CancelResponse
from app.services.cancel_engine import CancelEngine

router = APIRouter(prefix="/api/v1/orders", tags=["orders"])
engine = CancelEngine()


async def ensure_order_owner(db: AsyncSession, order_id: UUID, user_id: UUID) -> None:
    exists = await db.scalar(
        select(Order.id)
        .join(TradingAccount, TradingAccount.id == Order.account_id)
        .where(Order.id == order_id, TradingAccount.user_id == user_id)
    )
    if exists is None:
        raise HTTPException(status_code=404, detail="Order not found")


@router.post("/{order_id}/cancel", response_model=CancelResponse)
async def request_cancel(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CancelResponse:
    await ensure_order_owner(db, order_id, user.id)
    try:
        result = await engine.request_cancel(db, order_id=order_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CancelResponse(order_id=result.order_id, status=result.status.value)


@router.post("/{order_id}/cancel/confirm", response_model=CancelResponse)
async def confirm_cancel(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CancelResponse:
    await ensure_order_owner(db, order_id, user.id)
    try:
        result = await engine.confirm_cancel(db, order_id=order_id)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return CancelResponse(order_id=result.order_id, status=result.status.value)
