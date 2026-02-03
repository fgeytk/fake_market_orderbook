import pytest

from core import Order, OrderType, Side


def test_limit_order_valid():
    order = Order(id=1, side=Side.BID, type=OrderType.LIMIT, quantity=10, price_tick=100)
    assert order.price_tick == 100
    assert order.quantity == 10


def test_market_order_no_price_tick():
    order = Order(id=1, side=Side.ASK, type=OrderType.MARKET, quantity=5)
    assert order.price_tick is None


@pytest.mark.parametrize(
    "order_kwargs",
    [
        {"id": 1, "side": Side.BID, "type": OrderType.LIMIT, "quantity": 10, "price_tick": 0},
        {"id": 1, "side": Side.ASK, "type": OrderType.MARKET, "quantity": 5, "price_tick": 100},
        {"id": 1, "side": Side.BID, "type": OrderType.LIMIT, "quantity": 0, "price_tick": 100},
    ],
)
def test_invalid_orders_rejected(order_kwargs):
    with pytest.raises(ValueError):
        Order(**order_kwargs)
