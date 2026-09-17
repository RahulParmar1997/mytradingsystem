from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.order import Order, OrderSide
from app.models.risk import RiskLimit
from app.models.trading import Position, TradingAccount
from app.models.user import User
from app.risk.engine import RiskEngine, RiskLimits
from app.schemas.risk import RiskCheckRequest, RiskCheckResponse
from app.schemas.risk_limits import RiskLimitsResponse, RiskLimitsUpdate

router = APIRouter(prefix="/api/v1/risk", tags=["risk"])


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


async def get_account(account_id: UUID, user: User, db: AsyncSession) -> TradingAccount:
    account = await db.scalar(
        select(TradingAccount).where(TradingAccount.id == account_id, TradingAccount.user_id == user.id)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Trading account not found")
    return account


@router.get("/accounts/{account_id}/limits", response_model=RiskLimitsResponse)
async def get_risk_limits(
    account_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskLimit:
    account = await get_account(account_id, user, db)
    limits = await db.scalar(select(RiskLimit).where(RiskLimit.account_id == account.id))
    if limits is None:
        limits = RiskLimit(account_id=account.id)
        db.add(limits)
        await db.commit()
        await db.refresh(limits)
    return limits


@router.put("/accounts/{account_id}/limits", response_model=RiskLimitsResponse)
async def update_risk_limits(
    account_id: UUID,
    payload: RiskLimitsUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskLimit:
    account = await get_account(account_id, user, db)
    limits = await db.scalar(select(RiskLimit).where(RiskLimit.account_id == account.id).with_for_update())
    if limits is None:
        limits = RiskLimit(account_id=account.id)
        db.add(limits)
    limits.max_order_notional = payload.max_order_notional
    limits.max_position_notional = payload.max_position_notional
    limits.max_daily_loss = payload.max_daily_loss
    limits.max_open_orders = payload.max_open_orders
    await db.commit()
    await db.refresh(limits)
    return limits


@router.post("/accounts/{account_id}/check", response_model=RiskCheckResponse)
async def check_order_risk(
    account_id: UUID,
    payload: RiskCheckRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RiskCheckResponse:
    account = await get_account(account_id, user, db)
    position = await db.scalar(
        select(Position).where(Position.account_id == account.id, Position.symbol == payload.symbol.upper())
    )
    open_order_count = payload.open_order_count
    if open_order_count is None:
        open_order_count = await db.scalar(
            select(func.count(Order.id)).where(
                Order.account_id == account.id,
                Order.status.in_(["PENDING", "ACCEPTED", "PARTIALLY_FILLED", "CANCEL_PENDING"]),
            )
        )
    limits = await db.scalar(select(RiskLimit).where(RiskLimit.account_id == account.id))
    decision = build_engine(limits).evaluate_order(
        account=account,
        side=OrderSide(payload.side),
        quantity=payload.quantity,
        price=payload.price,
        position=position,
        open_order_count=int(open_order_count or 0),
    )
    return RiskCheckResponse(approved=decision.approved, reasons=list(decision.reasons))
