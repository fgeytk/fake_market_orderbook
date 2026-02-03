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
) -> Iterator[tuple[Order, list[Trade]]]:
    rng = random.Random(seed)
    next_id = 1
    t = 0
    mid_price = start_price

    while True:
        # random walk for mid price
        mid_price += rng.uniform(-0.05, 0.05)
        mid_price = max(0.01, mid_price)

        side = Side.BID if rng.random() < 0.5 else Side.ASK
        is_market = rng.random() < market_ratio
        qty = rng.randint(1, 50)

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
            price = mid_price - spread / 2 if side == Side.BID else mid_price + spread / 2
            order = Order(
                id=next_id,
                side=side,
                type=OrderType.LIMIT,
                quantity=qty,
                price=round(max(0.01, price), 2),
                timestamp=t,
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
