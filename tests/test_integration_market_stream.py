from __future__ import annotations

from dataclasses import asdict

from core import Orderbook, Order, Trade, CancelEvent
from simulation.market_stream import stream_fake_market


def serialize_event(event: Order | CancelEvent, trades: list[Trade]) -> tuple:
    event_dict = asdict(event)
    trade_dicts = [asdict(t) for t in trades]
    return (event.__class__.__name__, event_dict, trade_dicts)


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
        event, trades = next(gen)
        _ = (event, trades)

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
            event, trades = next(gen)
            out.append(serialize_event(event, trades))
        return out

    first = run_once()
    second = run_once()
    assert first == second
