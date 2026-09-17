from decimal import Decimal

from pydantic import BaseModel, Field


class RiskCheckRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32)
    side: str = Field(pattern="^(BUY|SELL)$")
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    open_order_count: int | None = Field(default=None, ge=0)


class RiskCheckResponse(BaseModel):
    approved: bool
    reasons: list[str]
