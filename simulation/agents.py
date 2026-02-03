"""Trading agents for synthetic order flow."""

from __future__ import annotations

from dataclasses import dataclass
import time
from typing import Iterable

from core import Order, OrderType, Side, Orderbook


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
    """Base class for trading agents."""

    name: str = "agent"

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = True,
    ) -> tuple[list[Order], int]:
        return [], next_id


@dataclass(slots=True)
class MarketMaker(BaseAgent):
    """Places both bid and ask around the mid price."""
    name: str = "market_maker"
    spread_ticks: int = 2
    size: int = 5

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = True,
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


@dataclass(slots=True)
class MomentumTrader(BaseAgent):
    """Trades with the momentum signal (market orders)."""
    name: str = "momentum"
    threshold: float = 0.003
    size: int = 5

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = True,
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


@dataclass(slots=True)
class MeanReversionTrader(BaseAgent):
    """Trades against large deviations from a reference price."""
    name: str = "mean_reversion"
    ref_price: float = 10.0
    threshold: float = 0.02
    size: int = 5

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = True,
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


@dataclass(slots=True)
class NoiseTrader(BaseAgent):
    """Random small orders around the mid price."""
    name: str = "noise"
    size: int = 3
    spread_ticks: int = 4

    def generate_orders(
        self,
        book: Orderbook,
        ctx: AgentContext,
        next_id: int,
        validate_orders: bool = True,
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
    validate_orders: bool = True,
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

    t = 0
    while True:
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

        # tiny drift for momentum signal
        momentum = 0.9 * momentum + 0.001
        mid_price = max(0.01, mid_price * (1.0 + 0.001))
        t += 1
        


if __name__ == "__main__":
    main()
