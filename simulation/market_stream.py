"""Realistic market data generator with regime switching."""

from __future__ import annotations

import sys
import time
import random
from dataclasses import asdict
from pathlib import Path
from typing import Iterator

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from core import Order, Trade, OrderType, Side, CancelEvent, Orderbook


def stream_fake_market(
    book: Orderbook,
    start_price: float = 10.0,
    spread: float = 0.5,
    seed: int = 42,
    market_ratio: float = 0.2,
    sleep_sec: float = 0.1,
    regime_switch_prob: float = 0.01,
    cancel_ratio: float = 0.3,
    orders_per_tick: int = 10,
    replenish: bool = True,
    validate_orders: bool = False,
) -> Iterator[tuple[Order | CancelEvent, list[Trade]]]:
    """
    Generate a realistic stream of market events with regime switching.
    
    Yields tuples of (Order/CancelEvent, list of trades executed).
    
    Regimes:
    - calm: Low volatility, tight spread, few market orders
    - normal: Medium volatility, normal spread
    - stress: High volatility, wide spread, many market orders
    validate_orders=False skips Order validation for higher throughput.
    """
    rng = random.Random(seed)
    rnd = rng.random
    gauss = rng.gauss
    lognorm = rng.lognormvariate
    expov = rng.expovariate
    choice = rng.choice
    uniform = rng.uniform
    next_id = 1
    t = 0
    mid_price = start_price
    momentum = 0.0
    regimes = {
        "calm": {
            "sigma": 0.003,
            "jump_prob": 0.001,
            "jump_sigma": 0.02,
            "spread_mult": 0.8,
            "market_ratio": 0.1,
            "imbalance": 0.02,
        },
        "normal": {
            "sigma": 0.01,
            "jump_prob": 0.003,
            "jump_sigma": 0.05,
            "spread_mult": 1.0,
            "market_ratio": 0.2,
            "imbalance": 0.0,
        },
        "stress": {
            "sigma": 0.03,
            "jump_prob": 0.01,
            "jump_sigma": 0.12,
            "spread_mult": 1.8,
            "market_ratio": 0.35,
            "imbalance": -0.05,
        },
    }
    regime_names = list(regimes.keys())
    regime = "normal"
    bid_keys_cache: list[int] = []
    ask_keys_cache: list[int] = []
    last_bid_levels = -1
    last_ask_levels = -1

    while True:
        if rnd() < regime_switch_prob:
            regime = choice(regime_names)

        params = regimes[regime]
        sigma = params["sigma"]
        jump_prob = params["jump_prob"]
        jump_sigma = params["jump_sigma"]
        spread_mult = params["spread_mult"]
        market_ratio_regime = params["market_ratio"]
        imbalance = params["imbalance"]

        # stochastic volatility random walk with occasional jumps
        shock = gauss(0.0, sigma)
        momentum = 0.95 * momentum + shock
        jump = 0.0
        if rnd() < jump_prob:
            jump = gauss(0.0, jump_sigma)

        mid_price *= max(0.01, 1.0 + shock + jump)
        mid_price = max(0.01, mid_price)

        for _ in range(max(1, orders_per_tick)):
            side_bias = 0.5 + imbalance + (0.08 if momentum > 0 else -0.08)
            side_bias = min(max(side_bias, 0.05), 0.95)
            side = Side.BID if rnd() < side_bias else Side.ASK

            effective_market_ratio = max(
                0.01, min(0.9, market_ratio * market_ratio_regime / 0.2)
            )
            is_market = rnd() < effective_market_ratio

            # heavy-tailed order sizes
            qty = int(max(1, min(500, lognorm(2.2, 0.8))))

            # occasional cancellations (observable)
            if rnd() < cancel_ratio:
                cancel_side = Side.BID if rnd() < 0.5 else Side.ASK
                if cancel_side == Side.BID:
                    levels = book.bids
                    if len(levels) != last_bid_levels:
                        bid_keys_cache = list(levels.keys())
                        last_bid_levels = len(levels)
                    if bid_keys_cache:
                        price_tick = choice(bid_keys_cache)
                        canceled = book.cancel_at_price(cancel_side, price_tick)
                        if canceled:
                            yield CancelEvent(cancel_side, price_tick, canceled.id), []
                else:
                    levels = book.asks
                    if len(levels) != last_ask_levels:
                        ask_keys_cache = list(levels.keys())
                        last_ask_levels = len(levels)
                    if ask_keys_cache:
                        price_tick = choice(ask_keys_cache)
                        canceled = book.cancel_at_price(cancel_side, price_tick)
                        if canceled:
                            yield CancelEvent(cancel_side, price_tick, canceled.id), []

            if is_market:
                order = Order(
                    id=next_id,
                    side=side,
                    type=OrderType.MARKET,
                    quantity=qty,
                    price_tick=None,
                    timestamp=t,
                    validate=validate_orders,
                )
            else:
                dynamic_spread = spread * spread_mult
                # concentrate liquidity near mid: exponential offset + small jitter
                base_offset = expov(1.0 / max(0.01, dynamic_spread * 0.35))
                offset = dynamic_spread / 2 + base_offset
                if rnd() < 0.6:
                    offset *= uniform(0.2, 0.6)

                price = mid_price - offset if side == Side.BID else mid_price + offset

                # liquidity clustering around round levels
                if rnd() < 0.5:
                    price = round(price * 20) / 20  # cluster to 0.05
                price_tick = book.price_to_tick(max(0.01, price))
                order = Order(
                    id=next_id,
                    side=side,
                    type=OrderType.LIMIT,
                    quantity=qty,
                    price_tick=price_tick,
                    timestamp=t,
                    validate=validate_orders,
                )

                # keep top of book close to mid by adding a replenishing order
                if replenish:
                    best_bid = book.best_bid()
                    best_ask = book.best_ask()
                    mid_tick = book.price_to_tick(mid_price)
                    max_gap_ticks = max(1, int(round((dynamic_spread * 2.5) / book.tick_size)))
                    if best_bid and abs(mid_tick - best_bid[0]) > max_gap_ticks:
                        repl = Order(
                            id=next_id + 10_000_000,
                            side=Side.BID,
                            type=OrderType.LIMIT,
                            quantity=max(1, qty // 2),
                            price_tick=max(1, mid_tick - max(1, int(round(dynamic_spread / (2 * book.tick_size))))),
                            timestamp=t,
                            validate=validate_orders,
                        )
                        repl_trades = book.add_order(repl)
                        yield repl, repl_trades
                    if best_ask and abs(best_ask[0] - mid_tick) > max_gap_ticks:
                        repl = Order(
                            id=next_id + 20_000_000,
                            side=Side.ASK,
                            type=OrderType.LIMIT,
                            quantity=max(1, qty // 2),
                            price_tick=mid_tick + max(1, int(round(dynamic_spread / (2 * book.tick_size)))),
                            timestamp=t,
                            validate=validate_orders,
                        )
                        repl_trades = book.add_order(repl)
                        yield repl, repl_trades

            next_id += 1
            t += 1

            trades = book.add_order(order)
            yield order, trades

        if sleep_sec > 0:
            time.sleep(sleep_sec)


def stream_fake_market_batch(
    book: Orderbook,
    batch_size: int = 100,
    **kwargs,
) -> Iterator[list[tuple[Order | CancelEvent, list[Trade]]]]:
    """Yield market events in batches for higher throughput."""
    generator = stream_fake_market(book, **kwargs)
    while True:
        batch: list[tuple[Order | CancelEvent, list[Trade]]] = []
        for _ in range(batch_size):
            batch.append(next(generator))
        yield batch


def main() -> None:
    """Simple test of the market stream."""
    from core import Orderbook
    book = Orderbook()

    for order, trades in stream_fake_market(book):
        print("EVENT:", asdict(order) if hasattr(order, '__dataclass_fields__') else order)
        for tr in trades:
            print("TRADE:", asdict(tr))


if __name__ == "__main__":
    main()
