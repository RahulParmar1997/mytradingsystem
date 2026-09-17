from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.risk import RiskLimit
from app.models.trading import TradingAccount
from app.models.user import User
from app.schemas.trading import AccountCreate, AccountResponse

router = APIRouter(prefix="/api/v1/accounts", tags=["accounts"])


@router.get("", response_model=list[AccountResponse])
async def list_accounts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> list[TradingAccount]:
    result = await db.scalars(select(TradingAccount).where(TradingAccount.user_id == user.id).order_by(TradingAccount.created_at))
    return list(result.all())


@router.post("", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(payload: AccountCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> TradingAccount:
    account = TradingAccount(
        user_id=user.id,
        name=payload.name,
        currency=payload.currency.upper(),
        initial_balance=payload.initial_balance,
        cash_balance=payload.initial_balance,
        realized_pnl=0,
    )
    db.add(account)
    await db.flush()
    db.add(RiskLimit(account_id=account.id))
    await db.commit()
    await db.refresh(account)
    return account


@router.get("/{account_id}", response_model=AccountResponse)
async def get_account(account_id: UUID, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)) -> TradingAccount:
    account = await db.scalar(select(TradingAccount).where(TradingAccount.id == account_id, TradingAccount.user_id == user.id))
    if not account:
        raise HTTPException(status_code=404, detail="Trading account not found")
    return account
