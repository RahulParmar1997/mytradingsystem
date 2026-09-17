import pytest

from app.models.order import OrderStatus
from app.services.order_state import validate_transition


def test_pending_can_be_accepted() -> None:
    validate_transition(OrderStatus.PENDING, OrderStatus.ACCEPTED)


def test_cancel_pending_can_fill_after_cancel_request() -> None:
    validate_transition(OrderStatus.CANCEL_PENDING, OrderStatus.FILLED)


def test_cancel_pending_can_partially_fill_after_cancel_request() -> None:
    validate_transition(OrderStatus.CANCEL_PENDING, OrderStatus.PARTIALLY_FILLED)


def test_cancel_pending_can_confirm_cancel() -> None:
    validate_transition(OrderStatus.CANCEL_PENDING, OrderStatus.CANCELLED)


def test_cancel_pending_cannot_revert_to_accepted() -> None:
    with pytest.raises(ValueError):
        validate_transition(OrderStatus.CANCEL_PENDING, OrderStatus.ACCEPTED)


def test_filled_is_terminal() -> None:
    with pytest.raises(ValueError):
        validate_transition(OrderStatus.FILLED, OrderStatus.CANCELLED)


def test_cancelled_is_terminal() -> None:
    with pytest.raises(ValueError):
        validate_transition(OrderStatus.CANCELLED, OrderStatus.ACCEPTED)
