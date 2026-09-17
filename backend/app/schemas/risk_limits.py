from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RiskLimitsUpdate(BaseModel):
    max_order_notional: Decimal = Field(gt=0)
    max_position_notional: Decimal = Field(gt=0)
    max_daily_loss: Decimal = Field(gt=0)
    max_open_orders: int = Field(gt=0, le=10000)


class RiskLimitsResponse(RiskLimitsUpdate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
