from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


class FillCreate(BaseModel):
    execution_id: str = Field(min_length=1, max_length=128)
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    fee: Decimal = Field(default=Decimal("0"), ge=0)


class FillResponse(BaseModel):
    id: UUID
    order_id: UUID
    account_id: UUID
    execution_id: str
    symbol: str
    quantity: Decimal
    price: Decimal
    fee: Decimal
    executed_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
