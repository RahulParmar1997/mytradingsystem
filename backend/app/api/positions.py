from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.core.database import get_db
from app.models.trading import Position, TradingAccount
from app.models.user import User

router = APIRouter(prefix="/api/v1/accounts", tags=["positions"])


@router.get("/{account_id}/positions")
async def list_positions(
    account_id: UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[Position]:
    account = await db.scalar(
        select(TradingAccount.id).where(
            TradingAccount.id == account_id,
            TradingAccount.user_id == user.id,
        )
    )
    if account is None:
        raise HTTPException(status_code=404, detail="Trading account not found")
    result = await db.scalars(
        select(Position).where(Position.account_id == account_id).order_by(Position.symbol)
    )
    return list(result.all())
