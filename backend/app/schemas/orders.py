from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.order import OrderSide, OrderStatus, OrderType, TimeInForce


class OrderCreate(BaseModel):
    account_id: UUID
    client_order_id: str = Field(min_length=1, max_length=64)
    symbol: str = Field(min_length=1, max_length=32)
    side: OrderSide
    order_type: OrderType
    time_in_force: TimeInForce = TimeInForce.DAY
    quantity: Decimal = Field(gt=0)
    limit_price: Decimal | None = Field(default=None, gt=0)
    stop_price: Decimal | None = Field(default=None, gt=0)

    @model_validator(mode="after")
    def validate_prices(self) -> "OrderCreate":
        if self.order_type in {OrderType.LIMIT, OrderType.STOP_LIMIT} and self.limit_price is None:
            raise ValueError("limit_price is required for limit orders")
        if self.order_type in {OrderType.STOP, OrderType.STOP_LIMIT} and self.stop_price is None:
            raise ValueError("stop_price is required for stop orders")
        if self.order_type == OrderType.MARKET and (self.limit_price is not None or self.stop_price is not None):
            raise ValueError("market orders cannot specify limit_price or stop_price")
        return self


class OrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    account_id: UUID
    client_order_id: str
    symbol: str
    side: OrderSide
    order_type: OrderType
    time_in_force: TimeInForce
    quantity: Decimal
    limit_price: Decimal | None
    stop_price: Decimal | None
    filled_quantity: Decimal
    average_fill_price: Decimal | None
    status: OrderStatus
    rejection_reason: str | None
