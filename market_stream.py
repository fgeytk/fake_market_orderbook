from __future__ import annotations

import time
import random
from dataclasses import asdict
from typing import Iterator

from main import Order, OrderType, Side, Trade, Orderbook


def stream_fake_market(
    book: Orderbook,
    start_price: float = 10.0,
    spread: float = 0.5,
    seed: int = 42,
    market_ratio: float = 0.2,
    sleep_sec: float = 0.1,
    regime_switch_prob: float = 0.01,
    cancel_ratio: float = 0.15,
    orders_per_tick: int = 100,
) -> Iterator[tuple[Order, list[Trade]]]:
    rng = random.Random(seed)
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

    while True:
        if rng.random() < regime_switch_prob:
            regime = rng.choice(regime_names)

        params = regimes[regime]

        # stochastic volatility random walk with occasional jumps
        shock = rng.gauss(0.0, params["sigma"])
        momentum = 0.95 * momentum + shock
        jump = 0.0
        if rng.random() < params["jump_prob"]:
            jump = rng.gauss(0.0, params["jump_sigma"])

        mid_price *= max(0.01, 1.0 + shock + jump)
        mid_price = max(0.01, mid_price)

        for _ in range(max(1, orders_per_tick)):
            side_bias = 0.5 + params["imbalance"] + (0.08 if momentum > 0 else -0.08)
            side_bias = min(max(side_bias, 0.05), 0.95)
            side = Side.BID if rng.random() < side_bias else Side.ASK

            effective_market_ratio = max(
                0.01, min(0.9, market_ratio * params["market_ratio"] / 0.2)
            )
            is_market = rng.random() < effective_market_ratio

            # heavy-tailed order sizes
            qty = int(max(1, min(500, rng.lognormvariate(2.2, 0.8))))

            # occasional cancellations to avoid book drift/overfill
            if rng.random() < cancel_ratio:
                if book.bids and rng.random() < 0.5:
                    price = rng.choice(list(book.bids.keys()))
                    q = book.bids.get(price)
                    if q:
                        q.popleft()
                        if not q:
                            del book.bids[price]
                elif book.asks:
                    price = rng.choice(list(book.asks.keys()))
                    q = book.asks.get(price)
                    if q:
                        q.popleft()
                        if not q:
                            del book.asks[price]

            if is_market:
                order = Order(
                    id=next_id,
                    side=side,
                    type=OrderType.MARKET,
                    quantity=qty,
                    price=None,
                    timestamp=t,
                )
            else:
                dynamic_spread = spread * params["spread_mult"]
                # concentrate liquidity near mid: exponential offset + small jitter
                base_offset = rng.expovariate(1.0 / max(0.01, dynamic_spread * 0.35))
                offset = dynamic_spread / 2 + base_offset
                if rng.random() < 0.6:
                    offset *= rng.uniform(0.2, 0.6)

                price = mid_price - offset if side == Side.BID else mid_price + offset

                # liquidity clustering around round levels
                if rng.random() < 0.5:
                    price = round(price * 20) / 20  # cluster to 0.05
                order = Order(
                    id=next_id,
                    side=side,
                    type=OrderType.LIMIT,
                    quantity=qty,
                    price=round(max(0.01, price), 2),
                    timestamp=t,
                )

                # keep top of book close to mid by adding a replenishing order
                best_bid = book.best_bid()
                best_ask = book.best_ask()
                max_gap = dynamic_spread * 2.5
                if best_bid and abs(mid_price - best_bid[0]) > max_gap:
                    book.add_order(
                        Order(
                            id=next_id + 10_000_000,
                            side=Side.BID,
                            type=OrderType.LIMIT,
                            quantity=max(1, qty // 2),
                            price=round(max(0.01, mid_price - dynamic_spread / 2), 2),
                            timestamp=t,
                        )
                    )
                if best_ask and abs(best_ask[0] - mid_price) > max_gap:
                    book.add_order(
                        Order(
                            id=next_id + 20_000_000,
                            side=Side.ASK,
                            type=OrderType.LIMIT,
                            quantity=max(1, qty // 2),
                            price=round(max(0.01, mid_price + dynamic_spread / 2), 2),
                            timestamp=t,
                        )
                    )

            next_id += 1
            t += 1

            trades = book.add_order(order)
            yield order, trades

        if sleep_sec > 0:
            time.sleep(sleep_sec)


def main() -> None:
    book = Orderbook()

    for order, trades in stream_fake_market(book):
        print("ORDER:", asdict(order))
        for tr in trades:
            print("TRADE:", asdict(tr))


if __name__ == "__main__":
    main()
