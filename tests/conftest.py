import pytest

from core import Orderbook, Order, OrderType, Side


@pytest.fixture
def book() -> Orderbook:
    return Orderbook()


@pytest.fixture
def make_limit():
    def _make_limit(order_id: int, side: Side, qty: int, price_tick: int) -> Order:
        return Order(
            id=order_id,
            side=side,
            type=OrderType.LIMIT,
            quantity=qty,
            price_tick=price_tick,
        )

    return _make_limit


@pytest.fixture
def make_market():
    def _make_market(order_id: int, side: Side, qty: int) -> Order:
        return Order(
            id=order_id,
            side=side,
            type=OrderType.MARKET,
            quantity=qty,
            price_tick=None,
        )

    return _make_market
