import pytest

from core import Side


def test_price_to_tick_rejects_non_positive(book):
    with pytest.raises(ValueError):
        book.price_to_tick(0)


def test_tick_to_price_roundtrip(book):
    price = 12.34
    tick = book.price_to_tick(price)
    roundtrip = book.tick_to_price(tick)
    assert roundtrip == pytest.approx(tick * book.tick_size)


def test_fifo_at_price_level(book, make_limit, make_market):
    book.add_limit(make_limit(1, Side.ASK, 2, 100))
    book.add_limit(make_limit(2, Side.ASK, 2, 100))

    trades = book.add_order(make_market(3, Side.BID, 3))
    assert [t.maker_id for t in trades] == [1, 2]
    assert [t.quantity for t in trades] == [2, 1]


def test_market_traverses_multiple_levels_with_partial_fill(book, make_limit, make_market):
    book.add_limit(make_limit(1, Side.ASK, 2, 100))
    book.add_limit(make_limit(2, Side.ASK, 3, 101))

    trades = book.add_order(make_market(3, Side.BID, 4))
    assert [(t.maker_id, t.price_tick, t.quantity) for t in trades] == [
        (1, 100, 2),
        (2, 101, 2),
    ]
    assert book.best_ask() == (101, 1)


def test_volume_conservation_after_trades(book, make_limit, make_market):
    book.add_limit(make_limit(1, Side.ASK, 5, 100))
    book.add_limit(make_limit(2, Side.ASK, 5, 101))

    trades = book.add_order(make_market(3, Side.BID, 7))
    traded_qty = sum(t.quantity for t in trades)
    remaining_qty = sum(book.ask_sizes.values())
    assert traded_qty == 7
    assert remaining_qty == 3


def test_market_on_empty_book_no_trades_and_no_levels(book, make_market):
    trades = book.add_order(make_market(1, Side.BID, 5))
    assert trades == []
    assert book.best_bid() is None
    assert book.best_ask() is None
    assert book.bids == {}
    assert book.asks == {}


def test_market_order_does_not_rest(book, make_market):
    book.add_order(make_market(1, Side.BID, 5))
    assert book.bids == {}
    assert book.asks == {}


def test_cancel_by_id_missing_is_false(book):
    assert book.cancel_by_id(12345) is False


def test_cancel_at_price_empty_returns_none(book):
    assert book.cancel_at_price(Side.ASK, 999) is None


def test_add_limit_rejects_market_order(book, make_market):
    with pytest.raises(ValueError):
        book.add_limit(make_market(1, Side.BID, 5))


def test_add_limit_and_best_prices(book, make_limit):
    book.add_limit(make_limit(1, Side.BID, 5, 100))
    book.add_limit(make_limit(2, Side.ASK, 7, 105))

    assert book.best_bid() == (100, 5)
    assert book.best_ask() == (105, 7)


def test_market_match_removes_levels(book, make_limit, make_market):
    book.add_limit(make_limit(1, Side.ASK, 5, 100))

    trades = book.add_order(make_market(2, Side.BID, 5))
    assert len(trades) == 1
    assert trades[0].price_tick == 100
    assert trades[0].quantity == 5
    assert book.best_ask() is None


def test_limit_aggressive_match_and_remainder_posts(book, make_limit):
    book.add_limit(make_limit(1, Side.ASK, 4, 100))

    trades = book.add_order(make_limit(2, Side.BID, 10, 100))
    assert len(trades) == 1
    assert trades[0].quantity == 4
    assert book.best_ask() is None
    assert book.best_bid() == (100, 6)


def test_cancel_by_id(book, make_limit):
    book.add_limit(make_limit(1, Side.BID, 5, 100))
    book.add_limit(make_limit(2, Side.BID, 5, 100))

    removed = book.cancel_by_id(1)
    assert removed is True
    assert book.best_bid() == (100, 5)


def test_cancel_at_price(book, make_limit):
    book.add_limit(make_limit(1, Side.ASK, 3, 105))
    book.add_limit(make_limit(2, Side.ASK, 3, 105))

    canceled = book.cancel_at_price(Side.ASK, 105)
    assert canceled is not None
    assert canceled.id == 1
    assert book.best_ask() == (105, 3)


def test_cancel_middle_of_price_level_keeps_fifo(book, make_limit):
    book.add_limit(make_limit(1, Side.BID, 2, 100))
    book.add_limit(make_limit(2, Side.BID, 2, 100))
    book.add_limit(make_limit(3, Side.BID, 2, 100))

    removed = book.cancel_by_id(2)
    assert removed is True

    queue_ids = [o.id for o in book.bids[100]]
    assert queue_ids == [1, 3]
    assert book.bid_sizes[100] == 4


def test_order_index_consistent_after_cancel_and_trade(book, make_limit, make_market):
    book.add_limit(make_limit(1, Side.ASK, 2, 100))
    book.add_limit(make_limit(2, Side.ASK, 2, 101))
    book.add_limit(make_limit(3, Side.ASK, 2, 102))

    assert 1 in book.order_index
    assert 2 in book.order_index
    assert 3 in book.order_index

    book.cancel_by_id(2)
    trades = book.add_order(make_market(4, Side.BID, 3))
    _ = trades

    assert 1 not in book.order_index
    assert 2 not in book.order_index
    assert 3 in book.order_index


def test_limit_crosses_multiple_levels_then_posts_remainder(book, make_limit):
    book.add_limit(make_limit(1, Side.ASK, 2, 100))
    book.add_limit(make_limit(2, Side.ASK, 2, 101))

    trades = book.add_order(make_limit(3, Side.BID, 5, 102))
    assert [(t.maker_id, t.price_tick, t.quantity) for t in trades] == [
        (1, 100, 2),
        (2, 101, 2),
    ]
    assert book.best_bid() == (102, 1)


def test_sizes_after_cancel_reflect_remaining_quantity(book, make_limit):
    book.add_limit(make_limit(1, Side.ASK, 3, 105))
    book.add_limit(make_limit(2, Side.ASK, 4, 105))

    removed = book.cancel_by_id(1)
    assert removed is True
    assert book.ask_sizes[105] == 4
