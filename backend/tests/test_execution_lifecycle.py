from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4

from app.services.execution_engine import ExecutionEngine
from app.services.paper_broker import PaperExecution


def test_paper_execution_carries_execution_timestamp() -> None:
    executed_at = datetime(2026, 9, 17, 12, 30, tzinfo=timezone.utc)
    execution = PaperExecution(
        order_id=uuid4(),
        execution_id="exec-1",
        quantity=Decimal("2"),
        price=Decimal("100"),
        executed_at=executed_at,
    )

    assert execution.executed_at == executed_at


def test_execution_engine_allows_cancel_pending() -> None:
    assert ExecutionEngine._EXECUTABLE_STATUSES
    from app.models.order import OrderStatus

    assert OrderStatus.CANCEL_PENDING in ExecutionEngine._EXECUTABLE_STATUSES
