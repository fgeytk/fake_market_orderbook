from core import Order, OrderType, Side
import pytest


def test_limit_order_valid():
    order = Order(id=1, side=Side.BID, type=OrderType.LIMIT, quantity=10, price_tick=100)
    assert order.price_tick == 100
    assert order.quantity == 10


def test_market_order_no_price_tick():
    order = Order(id=1, side=Side.ASK, type=OrderType.MARKET, quantity=5)
    assert order.price_tick is None


def test_limit_order_invalid_price_tick():
    with pytest.raises(ValueError):
        Order(id=1, side=Side.BID, type=OrderType.LIMIT, quantity=10, price_tick=0)


def test_market_order_with_price_tick_rejected():
    with pytest.raises(ValueError):
        Order(id=1, side=Side.ASK, type=OrderType.MARKET, quantity=5, price_tick=100)


def test_invalid_quantity_rejected():
    with pytest.raises(ValueError):
        Order(id=1, side=Side.BID, type=OrderType.LIMIT, quantity=0, price_tick=100)
