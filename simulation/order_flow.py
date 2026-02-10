"""Random order‑flow generation and L3 message emission helpers."""

from __future__ import annotations

import random
from typing import Iterator, TYPE_CHECKING

from core import Order, OrderType, Side, Orderbook, L3Add, L3Execute, L3Cancel

if TYPE_CHECKING:
    from simulation.agents import BaseAgent


# ---------------------------------------------------------------------------
# L3 emit helpers — factor out the repetitive yield patterns
# ---------------------------------------------------------------------------

def emit_order(
    book: Orderbook,
    order: Order,
    t: int,
) -> Iterator[tuple[L3Add | L3Execute | L3Cancel, int]]:
    """Submit *order* to the book and yield L3 messages.

    Yields ``(message, new_t)`` tuples so the caller can update its
    local timestamp counter.
    """
    original_price_tick = order.price_tick

    trades = book.add_order(order)

    for trade in trades:
        t += 1
        yield L3Execute(
            timestamp=float(t),
            maker_id=trade.maker_id,
            price_tick=trade.price_tick,
            price=book.tick_to_price(trade.price_tick),
            quantity=trade.quantity,
            aggressor_side=order.side.value,
        ), t

    if order.type == OrderType.LIMIT and order.quantity > 0:
        t += 1
        yield L3Add(
            timestamp=float(t),
            order_id=order.id,
            side=order.side.value,
            price_tick=original_price_tick,
            price=book.tick_to_price(original_price_tick),
            quantity=order.quantity,
        ), t


def try_cancel_owned(
    book: Orderbook,
    all_agents: list[BaseAgent],
    mid_tick: int,
    rng: random.Random,
    t: int,
) -> tuple[L3Cancel | None, int]:
    """An agent cancels one of its own orders.

    Picks a random agent (weighted by live order count),
    then the agent picks one of its own orders to cancel — farther
    orders from mid are more likely to be pulled.

    Returns ``(msg_or_None, new_t)``.
    """
    active = [a for a in all_agents if a.live_orders]
    if not active:
        return None, t

    weights = [len(a.live_orders) for a in active]
    agent = rng.choices(active, weights, k=1)[0]

    order_id = agent.pick_cancel(book, mid_tick, rng)
    if order_id is None:
        return None, t

    info = book.order_index.get(order_id)
    if info is None:
        agent.on_order_removed(order_id)
        return None, t

    side, price_tick = info
    # look up quantity
    queue = (book.bids if side == Side.BID else book.asks).get(price_tick)
    qty = 0
    if queue:
        for o in queue:
            if o.id == order_id:
                qty = o.quantity
                break

    if not book.cancel_by_id(order_id):
        return None, t

    agent.on_order_removed(order_id)
    t += 1
    return L3Cancel(
        timestamp=float(t),
        order_id=order_id,
        side=side.value,
        price_tick=price_tick,
        price=book.tick_to_price(price_tick),
        cancelled_quantity=qty,
    ), t


# ---------------------------------------------------------------------------
# Random order factory
# ---------------------------------------------------------------------------

def make_random_order(
    rng: random.Random,
    next_id: int,
    side: Side,
    is_market: bool,
    mid_price: float,
    spread: float,
    spread_mult: float,
    min_price: float,
    min_tick: int,
    book: Orderbook,
    t: int,
    validate: bool,
) -> Order:
    """Create one random order (market or limit)."""
    qty = int(max(1, min(500, rng.lognormvariate(2.2, 0.8))))

    if is_market:
        return Order(
            id=next_id,
            side=side,
            type=OrderType.MARKET,
            quantity=qty,
            price_tick=None,
            timestamp=t,
            validate=validate,
        )

    dynamic_spread = spread * spread_mult
    base_offset = rng.expovariate(1.0 / max(0.01, dynamic_spread * 0.35))
    offset = dynamic_spread / 2 + base_offset
    if rng.random() < 0.6:
        offset *= rng.uniform(0.2, 0.6)

    price = mid_price - offset if side == Side.BID else mid_price + offset

    if rng.random() < 0.5:
        price = round(price * 20) / 20  # cluster to 0.05
    price_tick = max(min_tick, book.price_to_tick(max(min_price, price)))

    return Order(
        id=next_id,
        side=side,
        type=OrderType.LIMIT,
        quantity=qty,
        price_tick=price_tick,
        timestamp=t,
        validate=validate,
    )


# ---------------------------------------------------------------------------
# Replenish top-of-book
# ---------------------------------------------------------------------------

def replenish_book(
    book: Orderbook,
    mid_price: float,
    spread: float,
    spread_mult: float,
    next_id: int,
    min_tick: int,
    rng: random.Random,
    t: int,
    validate: bool,
    owner_agent: BaseAgent | None = None,
) -> Iterator[tuple[L3Add | L3Execute, int, int]]:
    """If top of book drifted far from mid, post replenishing orders.

    Yields ``(message, new_t, new_next_id)`` tuples.
    """
    dynamic_spread = spread * spread_mult
    mid_tick = book.price_to_tick(mid_price)
    max_gap_ticks = max(1, int(round((dynamic_spread * 2.5) / book.tick_size)))
    half_spread_ticks = max(1, int(round(dynamic_spread / (2 * book.tick_size))))
    qty = int(max(1, min(200, rng.lognormvariate(2.0, 0.7))))

    best_bid = book.best_bid()
    if best_bid and abs(mid_tick - best_bid[0]) > max_gap_ticks:
        repl = Order(
            id=next_id + 10_000_000,
            side=Side.BID,
            type=OrderType.LIMIT,
            quantity=max(1, qty // 2),
            price_tick=max(min_tick, mid_tick - half_spread_ticks),
            timestamp=t,
            validate=validate,
        )
        for msg, t in emit_order(book, repl, t):
            yield msg, t, next_id
        if owner_agent is not None and repl.id in book.order_index:
            owner_agent.on_order_placed(repl.id)

    best_ask = book.best_ask()
    if best_ask and abs(best_ask[0] - mid_tick) > max_gap_ticks:
        repl = Order(
            id=next_id + 20_000_000,
            side=Side.ASK,
            type=OrderType.LIMIT,
            quantity=max(1, qty // 2),
            price_tick=mid_tick + half_spread_ticks,
            timestamp=t,
            validate=validate,
        )
        for msg, t in emit_order(book, repl, t):
            yield msg, t, next_id
        if owner_agent is not None and repl.id in book.order_index:
            owner_agent.on_order_placed(repl.id)
