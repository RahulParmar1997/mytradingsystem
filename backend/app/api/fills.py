from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.fill import Fill
from app.models.order import Order
from app.models.trading import TradingAccount
from app.models.user import User
from app.schemas.fills import FillCreate, FillResponse
from app.services.fill_service import FillService

router = APIRouter(prefix="/api/v1", tags=["fills"])
service = FillService()


@router.post("/orders/{order_id}/fills", response_model=FillResponse, status_code=201)
async def apply_order_fill(
    order_id: UUID,
    payload: FillCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FillResponse:
    order = await db.scalar(
        select(Order).join(TradingAccount, TradingAccount.id == Order.account_id).where(
            Order.id == order_id,
            TradingAccount.user_id == user.id,
        )
    )
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    try:
        fill = await service.apply_fill(
            db,
            order_id=order_id,
            execution_id=payload.execution_id,
            quantity=payload.quantity,
            price=payload.price,
            fee=payload.fee,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return FillResponse.model_validate(fill)


@router.get("/orders/{order_id}/fills", response_model=list[FillResponse])
async def list_order_fills(
    order_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[FillResponse]:
    owns_order = await db.scalar(
        select(Order.id).join(TradingAccount, TradingAccount.id == Order.account_id).where(
            Order.id == order_id,
            TradingAccount.user_id == user.id,
        )
    )
    if owns_order is None:
        raise HTTPException(status_code=404, detail="Order not found")

    result = await db.scalars(select(Fill).where(Fill.order_id == order_id).order_by(Fill.created_at.asc()))
    return [FillResponse.model_validate(fill) for fill in result.all()]
