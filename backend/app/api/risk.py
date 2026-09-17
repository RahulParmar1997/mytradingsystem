from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.order import Order, OrderSide
from app.models.trading import Position, TradingAccount
from app.models.user import User
from app.risk.engine import RiskEngine
from app.schemas.risk import RiskCheckRequest, RiskCheckResponse

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])
engine = RiskEngine()


@router.post("/accounts/{account_id}/check", response_model=RiskCheckResponse)
async def check_order_risk(
    account_id: UUID,
    payload: RiskCheckRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskCheckResponse:
    account = await db.scalar(
        select(TradingAccount).where(TradingAccount.id == account_id, TradingAccount.user_id == user.id)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Trading account not found")

    # The risk API requires a symbol only through the eventual order flow; this endpoint
    # validates account-level constraints using the current portfolio aggregate.
    open_order_count = await db.scalar(
        select(func.count(Order.id)).where(
            Order.account_id == account.id,
            Order.status.in_(["PENDING", "ACCEPTED", "PARTIALLY_FILLED", "CANCEL_PENDING"]),
        )
    )
    position = None
    decision = engine.evaluate_order(
        account=account,
        side=OrderSide(payload.side),
        quantity=payload.quantity,
        price=payload.price,
        position=position,
        open_order_count=int(open_order_count or 0),
    )
    return RiskCheckResponse(approved=decision.approved, reasons=list(decision.reasons))
