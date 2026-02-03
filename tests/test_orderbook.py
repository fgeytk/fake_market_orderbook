from core import Orderbook, Order, OrderType, Side


def make_limit(order_id: int, side: Side, qty: int, price_tick: int) -> Order:
    return Order(
        id=order_id,
        side=side,
        type=OrderType.LIMIT,
        quantity=qty,
        price_tick=price_tick,
    )


def make_market(order_id: int, side: Side, qty: int) -> Order:
    return Order(
        id=order_id,
        side=side,
        type=OrderType.MARKET,
        quantity=qty,
        price_tick=None,
    )


def test_price_to_tick_rejects_non_positive():
    book = Orderbook()
    import pytest

    with pytest.raises(ValueError):
        book.price_to_tick(0)


def test_add_limit_and_best_prices():
    book = Orderbook()
    book.add_limit(make_limit(1, Side.BID, 5, 100))
    book.add_limit(make_limit(2, Side.ASK, 7, 105))

    assert book.best_bid() == (100, 5)
    assert book.best_ask() == (105, 7)


def test_market_match_removes_levels():
    book = Orderbook()
    book.add_limit(make_limit(1, Side.ASK, 5, 100))

    trades = book.add_order(make_market(2, Side.BID, 5))
    assert len(trades) == 1
    assert trades[0].price_tick == 100
    assert trades[0].quantity == 5
    assert book.best_ask() is None


def test_limit_aggressive_match_and_remainder_posts():
    book = Orderbook()
    book.add_limit(make_limit(1, Side.ASK, 4, 100))

    trades = book.add_order(make_limit(2, Side.BID, 10, 100))
    assert len(trades) == 1
    assert trades[0].quantity == 4
    assert book.best_ask() is None
    assert book.best_bid() == (100, 6)


def test_cancel_by_id():
    book = Orderbook()
    book.add_limit(make_limit(1, Side.BID, 5, 100))
    book.add_limit(make_limit(2, Side.BID, 5, 100))

    removed = book.cancel_by_id(1)
    assert removed is True
    assert book.best_bid() == (100, 5)


def test_cancel_at_price():
    book = Orderbook()
    book.add_limit(make_limit(1, Side.ASK, 3, 105))
    book.add_limit(make_limit(2, Side.ASK, 3, 105))

    canceled = book.cancel_at_price(Side.ASK, 105)
    assert canceled is not None
    assert canceled.id == 1
    assert book.best_ask() == (105, 3)
