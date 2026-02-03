from __future__ import annotations

from collections import deque

from hypothesis import given, settings
from hypothesis import strategies as st

from core import Orderbook, Order, OrderType, Side


limit_order_data = st.tuples(
    st.sampled_from([Side.BID, Side.ASK]),
    st.just(OrderType.LIMIT),
    st.integers(min_value=1, max_value=50),
    st.integers(min_value=1, max_value=500),
)

market_order_data = st.tuples(
    st.sampled_from([Side.BID, Side.ASK]),
    st.just(OrderType.MARKET),
    st.integers(min_value=1, max_value=50),
    st.just(None),
)

order_data = st.one_of(limit_order_data, market_order_data)


@settings(max_examples=50, deadline=None)
@given(st.lists(order_data, min_size=1, max_size=200))
def test_orderbook_invariants_under_random_flow(order_sequence: list[tuple[Side, OrderType, int, int | None]]) -> None:
    book = Orderbook()

    for oid, (side, order_type, quantity, price_tick) in enumerate(order_sequence, start=1):
        order = Order(
            id=oid,
            side=side,
            type=order_type,
            quantity=quantity,
            price_tick=price_tick,
            validate=True,
        )
        book.add_order(order)

        best_bid = book.best_bid()
        best_ask = book.best_ask()
        if best_bid and best_ask:
            assert best_bid[0] < best_ask[0]

        for sizes in (book.bid_sizes, book.ask_sizes):
            assert all(qty >= 0 for qty in sizes.values())

        for levels in (book.bids, book.asks):
            for q in levels.values():
                assert isinstance(q, deque)
                for o in q:
                    assert o.quantity > 0
