from decimal import Decimal

from pydantic import BaseModel, Field


class RiskCheckRequest(BaseModel):
    side: str = Field(pattern="^(BUY|SELL)$")
    quantity: Decimal = Field(gt=0)
    price: Decimal = Field(gt=0)
    open_order_count: int = Field(default=0, ge=0)


class RiskCheckResponse(BaseModel):
    approved: bool
    reasons: list[str]
