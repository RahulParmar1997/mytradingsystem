import pytest

from app.models.order import OrderStatus
from app.services.order_state import validate_transition


def test_pending_can_be_accepted() -> None:
    validate_transition(OrderStatus.PENDING, OrderStatus.ACCEPTED)


def test_filled_is_terminal() -> None:
    with pytest.raises(ValueError):
        validate_transition(OrderStatus.FILLED, OrderStatus.CANCELLED)


def test_cancelled_is_terminal() -> None:
    with pytest.raises(ValueError):
        validate_transition(OrderStatus.CANCELLED, OrderStatus.ACCEPTED)
