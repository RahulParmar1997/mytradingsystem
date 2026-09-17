from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AccountCreate(BaseModel):
    name: str = Field(default="Primary Trading Account", min_length=1, max_length=120)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    initial_balance: Decimal = Field(default=Decimal("0"), ge=0)


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    currency: str
    initial_balance: Decimal
    cash_balance: Decimal
    realized_pnl: Decimal

