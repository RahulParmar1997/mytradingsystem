from uuid import UUID

from pydantic import BaseModel


class CancelResponse(BaseModel):
    order_id: UUID
    status: str
