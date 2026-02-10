"""Orderbook maintenance operations (seed, purge, clear)."""

from __future__ import annotations

import random
from typing import Iterator, TYPE_CHECKING

from core import Order, OrderType, Side, Orderbook, L3Cancel

if TYPE_CHECKING:
    from simulation.agents import BaseAgent


def clear_book(book: Orderbook) -> None:
    """Cancel every resting order (end-of-day clearing)."""
    for tick in list(book.bids.keys()):
        while book.bids.get(tick):
            book.cancel_at_price(Side.BID, tick)
    for tick in list(book.asks.keys()):
        while book.asks.get(tick):
            book.cancel_at_price(Side.ASK, tick)


def purge_stale_levels(
    book: Orderbook,
    mid_tick: int,
    max_distance_ticks: int,
) -> int:
    """Remove resting orders far from the current mid.

    Returns the number of orders purged.
    """
    purged = 0
    for tick in list(book.bids.keys()):
        if mid_tick - tick > max_distance_ticks:
            while book.bids.get(tick):
                book.cancel_at_price(Side.BID, tick)
                purged += 1
    for tick in list(book.asks.keys()):
        if tick - mid_tick > max_distance_ticks:
            while book.asks.get(tick):
                book.cancel_at_price(Side.ASK, tick)
                purged += 1
    return purged


def seed_book(
    book: Orderbook,
    mid_price: float,
    spread: float,
    rng: random.Random,
    next_id: int,
    n_levels: int = 20,
    orders_per_level: int = 4,
    validate: bool = False,
    agents: list[BaseAgent] | None = None,
) -> int:
    """Pre-seed the book with resting liquidity around *mid_price*.

    Creates *n_levels* price levels on each side with
    *orders_per_level* orders each (opening auction simulation).

    Returns the updated *next_id*.
    """
    mid_tick = book.price_to_tick(mid_price)
    min_tick = max(1, book.price_to_tick(book.tick_size))
    half_spread_ticks = max(1, book.price_to_tick(spread / 2))

    for i in range(n_levels):
        bid_tick = max(min_tick, mid_tick - half_spread_ticks - i)
        ask_tick = mid_tick + half_spread_ticks + i

        for _ in range(orders_per_level):
            qty = int(max(1, min(200, rng.lognormvariate(2.3, 0.6))))
            book.add_limit(Order(
                id=next_id,
                side=Side.BID,
                type=OrderType.LIMIT,
                quantity=qty,
                price_tick=bid_tick,
                timestamp=0,
                validate=validate,
            ))
            if agents:
                rng.choice(agents).on_order_placed(next_id)
            next_id += 1

            qty = int(max(1, min(200, rng.lognormvariate(2.3, 0.6))))
            book.add_limit(Order(
                id=next_id,
                side=Side.ASK,
                type=OrderType.LIMIT,
                quantity=qty,
                price_tick=ask_tick,
                timestamp=0,
                validate=validate,
            ))
            if agents:
                rng.choice(agents).on_order_placed(next_id)
            next_id += 1
    return next_id


def purge_stale_orders(
    book: Orderbook,
    all_agents: list[BaseAgent],
    mid_tick: int,
    max_distance_ticks: int,
    rng: random.Random,
    t: int,
) -> Iterator[tuple[L3Cancel, int]]:
    """Agent-driven stale order purge.

    Each agent independently reviews its own live orders and decides
    whether to pull those that are too far from mid.  Market-makers
    pull aggressively; noise traders may leave stale orders behind.

    Yields ``(L3Cancel, new_t)`` tuples.
    """
    for agent in all_agents:
        to_cancel = agent.pull_stale_orders(book, mid_tick, max_distance_ticks, rng)
        for order_id in to_cancel:
            info = book.order_index.get(order_id)
            if info is None:
                agent.on_order_removed(order_id)
                continue
            side, price_tick = info
            # look up quantity before cancelling
            queue = (book.bids if side == Side.BID else book.asks).get(price_tick)
            qty = 0
            if queue:
                for o in queue:
                    if o.id == order_id:
                        qty = o.quantity
                        break
            if book.cancel_by_id(order_id):
                agent.on_order_removed(order_id)
                t += 1
                yield L3Cancel(
                    timestamp=float(t),
                    order_id=order_id,
                    side=side.value,
                    price_tick=price_tick,
                    price=book.tick_to_price(price_tick),
                    cancelled_quantity=qty,
                ), t
