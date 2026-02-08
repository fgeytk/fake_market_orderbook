from __future__ import annotations

from dataclasses import asdict

from core import Orderbook, L3Add, L3Execute, L3Cancel
from simulation.market_stream import stream_fake_market


def serialize_msg(msg: L3Add | L3Execute | L3Cancel) -> tuple:
    msg_dict = asdict(msg)
    return (msg.__class__.__name__, msg_dict)


def test_market_stream_integration_sane_metrics():
    book = Orderbook()
    gen = stream_fake_market(
        book,
        seed=123,
        sleep_sec=0,
        orders_per_tick=5,
        cancel_ratio=0.2,
        validate_orders=True,
    )

    spreads = []
    total_depth = 0

    for _ in range(1000):
        msg = next(gen)
        _ = msg

        best_bid = book.best_bid()
        best_ask = book.best_ask()
        if best_bid and best_ask:
            assert best_bid[0] < best_ask[0]
            spreads.append(best_ask[0] - best_bid[0])

        total_depth += sum(book.bid_sizes.values()) + sum(book.ask_sizes.values())

    if spreads:
        avg_spread = sum(spreads) / len(spreads)
        assert 0 < avg_spread < 1_000

    assert total_depth > 0


def test_market_stream_deterministic_with_seed():
    def run_once() -> list[tuple]:
        book = Orderbook()
        gen = stream_fake_market(
            book,
            seed=999,
            sleep_sec=0,
            orders_per_tick=3,
            cancel_ratio=0.1,
            validate_orders=True,
        )
        out = []
        for _ in range(200):
            msg = next(gen)
            out.append(serialize_msg(msg))
        return out

    first = run_once()
    second = run_once()
    assert first == second
