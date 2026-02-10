"""Trading agents for synthetic order flow.

Each agent tracks the orders it places (``live_orders``) so that
cancellations and stale-order purges are always *owner-initiated* —
exactly like a real market.
"""

from __future__ import annotations

from dataclasses import dataclass, field
import time
import random
from typing import Iterable

from core import Order, OrderType, Side, Orderbook
from core.config import VALIDATE_ORDERS
from simulation.stochastic import evolve_mid_price


@dataclass(slots=True)
class AgentContext:
    """Snapshot of market state passed to agents."""
    t: int
    mid_price: float
    mid_tick: int
    best_bid: tuple[int, int] | None
    best_ask: tuple[int, int] | None
    momentum: float


class BaseAgent:
    """Base class for trading agents.

    Every agent keeps a ``live_orders`` set so it can cancel only its
    own orders — never someone else's.
    """

    name: str = "agent"
    cancel_aggressiveness: float = 0.5  # how keen to cancel stale orders

    def __init__(self) -> None:
        self.live_orders: set[int] = set()

    # ---- order generation ----

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = VALIDATE_ORDERS,
    ) -> tuple[list[Order], int]:
        return [], next_id

    # ---- ownership tracking ----

    def on_order_placed(self, order_id: int) -> None:
        """Register an order as belonging to this agent."""
        self.live_orders.add(order_id)

    def on_order_removed(self, order_id: int) -> None:
        """Notify that an order was filled or cancelled."""
        self.live_orders.discard(order_id)

    def _prune_dead(self, book: Orderbook) -> None:
        """Drop IDs that disappeared from the book (filled)."""
        gone = [oid for oid in self.live_orders if oid not in book.order_index]
        for oid in gone:
            self.live_orders.discard(oid)

    # ---- cancellation logic ----

    def pick_cancel(
        self,
        book: Orderbook,
        mid_tick: int,
        rng: random.Random,
    ) -> int | None:
        """Choose one of this agent's own orders to cancel.

        Orders further from the mid have a higher probability of being
        picked (distance² weighting).  Returns ``order_id`` or ``None``.
        """
        self._prune_dead(book)
        if not self.live_orders:
            return None

        scored: list[tuple[int, float]] = []
        for oid in self.live_orders:
            info = book.order_index.get(oid)
            if info is None:
                continue
            _, ptick = info
            dist = abs(ptick - mid_tick)
            scored.append((oid, max(1.0, float(dist * dist))))

        if not scored:
            return None

        oids, weights = zip(*scored)
        return rng.choices(list(oids), list(weights), k=1)[0]

    def pull_stale_orders(
        self,
        book: Orderbook,
        mid_tick: int,
        max_distance_ticks: int,
        rng: random.Random,
    ) -> list[int]:
        """Return list of this agent's order IDs that are too far from mid.

        Each stale order is pulled with probability proportional to
        ``cancel_aggressiveness``.
        """
        self._prune_dead(book)
        to_cancel: list[int] = []

        for oid in list(self.live_orders):
            info = book.order_index.get(oid)
            if info is None:
                continue
            _, price_tick = info
            dist = abs(price_tick - mid_tick)
            if dist <= max_distance_ticks:
                continue
            pull_prob = self.cancel_aggressiveness * min(
                1.0, dist / max_distance_ticks,
            )
            if rng.random() < pull_prob:
                to_cancel.append(oid)
        return to_cancel

    def clear(self) -> None:
        """Wipe all tracked orders (end of day)."""
        self.live_orders.clear()


@dataclass(slots=False)
class MarketMaker(BaseAgent):
    """Places both bid and ask around the mid price."""
    name: str = "market_maker"
    spread_ticks: int = 2
    size: int = 5
    cancel_aggressiveness: float = 0.95

    def __post_init__(self) -> None:
        self.live_orders: set[int] = set()

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = VALIDATE_ORDERS,
    ) -> tuple[list[Order], int]:
        bid_tick = max(1, ctx.mid_tick - self.spread_ticks)
        ask_tick = ctx.mid_tick + self.spread_ticks

        orders = [
            Order(
                id=next_id,
                side=Side.BID,
                type=OrderType.LIMIT,
                quantity=self.size,
                price_tick=bid_tick,
                timestamp=ctx.t,
                validate=validate_orders,
            ),
            Order(
                id=next_id + 1,
                side=Side.ASK,
                type=OrderType.LIMIT,
                quantity=self.size,
                price_tick=ask_tick,
                timestamp=ctx.t,
                validate=validate_orders,
            ),
        ]
        return orders, next_id + 2


@dataclass(slots=False)
class MomentumTrader(BaseAgent):
    """Trades with the momentum signal (market orders)."""
    name: str = "momentum"
    threshold: float = 0.003
    size: int = 5
    cancel_aggressiveness: float = 0.3

    def __post_init__(self) -> None:
        self.live_orders: set[int] = set()

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = VALIDATE_ORDERS,
    ) -> tuple[list[Order], int]:
        if ctx.momentum > self.threshold:
            side = Side.BID
        elif ctx.momentum < -self.threshold:
            side = Side.ASK
        else:
            return [], next_id

        order = Order(
            id=next_id,
            side=side,
            type=OrderType.MARKET,
            quantity=self.size,
            price_tick=None,
            timestamp=ctx.t,
            validate=validate_orders,
        )
        return [order], next_id + 1


@dataclass(slots=False)
class MeanReversionTrader(BaseAgent):
    """Trades against large deviations from a reference price."""
    name: str = "mean_reversion"
    ref_price: float = 10.0
    threshold: float = 0.02
    size: int = 5
    cancel_aggressiveness: float = 0.5

    def __post_init__(self) -> None:
        self.live_orders: set[int] = set()

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = VALIDATE_ORDERS,
    ) -> tuple[list[Order], int]:
        diff = (ctx.mid_price - self.ref_price) / self.ref_price
        if diff > self.threshold:
            side = Side.ASK
        elif diff < -self.threshold:
            side = Side.BID
        else:
            return [], next_id

        order = Order(
            id=next_id,
            side=side,
            type=OrderType.MARKET,
            quantity=self.size,
            price_tick=None,
            timestamp=ctx.t,
            validate=validate_orders,
        )
        return [order], next_id + 1


@dataclass(slots=False)
class NoiseTrader(BaseAgent):
    """Random small orders around the mid price."""
    name: str = "noise"
    size: int = 3
    spread_ticks: int = 4
    cancel_aggressiveness: float = 0.15

    def __post_init__(self) -> None:
        self.live_orders: set[int] = set()

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = False,
    ) -> tuple[list[Order], int]:
        side = Side.BID if (next_id % 2 == 0) else Side.ASK
        tick = ctx.mid_tick - self.spread_ticks if side == Side.BID else ctx.mid_tick + self.spread_ticks
        order = Order(
            id=next_id,
            side=side,
            type=OrderType.LIMIT,
            quantity=self.size,
            price_tick=max(1, tick),
            timestamp=ctx.t,
            validate=validate_orders,
        )
        return [order], next_id + 1


def generate_agent_orders(
    agents: Iterable[BaseAgent],
    book: Orderbook,
    ctx: AgentContext,
    next_id: int,
    validate_orders: bool = VALIDATE_ORDERS,
) -> tuple[list[Order], int]:
    """Aggregate orders from multiple agents."""
    orders: list[Order] = []
    for agent in agents:
        new_orders, next_id = agent.generate_orders(
            book,
            ctx,
            next_id,
            validate_orders=validate_orders,
        )
        if new_orders:
            orders.extend(new_orders)
    return orders, next_id


def main() -> None:
    """Quick smoke test: run only agent-generated orders."""
    book = Orderbook()
    agents: list[BaseAgent] = [
        MarketMaker(),
        MomentumTrader(),
        MeanReversionTrader(ref_price=10.0),
        NoiseTrader(),
    ]
    next_id = 1
    mid_price = 10.0
    momentum = 0.0
    rng = random.Random(42)
    regimes = {
        "calm": {
            "sigma": 0.003,
            "jump_prob": 0.001,
            "jump_sigma": 0.02,
        },
        "normal": {
            "sigma": 0.01,
            "jump_prob": 0.003,
            "jump_sigma": 0.05,
        },
        "stress": {
            "sigma": 0.03,
            "jump_prob": 0.01,
            "jump_sigma": 0.12,
        },
    }
    regime = "normal"

    t = 0
    while True:
        mid_price, momentum, regime = evolve_mid_price(
            rng,
            mid_price,
            momentum,
            regimes,
            regime,
            regime_switch_prob=0.01,
        )

        mid_tick = book.price_to_tick(mid_price)
        ctx = AgentContext(
            t=t,
            mid_price=mid_price,
            mid_tick=mid_tick,
            best_bid=book.best_bid(),
            best_ask=book.best_ask(),
            momentum=momentum,
        )
        orders, next_id = generate_agent_orders(
            agents, book, ctx, next_id, validate_orders=False
        )
        for order in orders:
            trades = book.add_order(order)
            print(f"{t:02d} | {order}")
            for tr in trades:
                print(f"   Trade: {tr}")

        t += 1
        


if __name__ == "__main__":
    main()
