"""Realistic market‑data generator — thin orchestrator.

All heavy logic is delegated to:
  - ``simulation.config``     → SimulationConfig
  - ``simulation.stochastic`` → price evolution & intraday curves
  - ``simulation.book_ops``   → seed / purge / clear
  - ``simulation.order_flow`` → random orders, cancels, replenish, L3 emit
  - ``simulation.agents``     → pluggable trading agents
"""

from __future__ import annotations

import sys
import time
import random
from pathlib import Path
from typing import Iterator

if __package__ in (None, ""):
    _root = Path(__file__).resolve().parents[1]
    if str(_root) not in sys.path:
        sys.path.insert(0, str(_root))

from core import Order, OrderType, Side, Orderbook, L3Add, L3Execute, L3Cancel
from simulation.config import SimulationConfig
from simulation.agents import AgentContext, BaseAgent, MarketMaker, NoiseTrader, generate_agent_orders
from simulation.stochastic import (
    evolve_mid_price,
    intraday_activity_factor,
    intraday_volatility_factor,
    overnight_gap,
    daily_drift,
)
from simulation.book_ops import clear_book, purge_stale_orders, seed_book
from simulation.order_flow import (
    emit_order,
    try_cancel_owned,
    make_random_order,
    replenish_book,
)


# ------------------------------------------------------------------
# Main generator
# ------------------------------------------------------------------

def stream_fake_market(
    book: Orderbook,
    cfg: SimulationConfig | None = None,
    agents: list[BaseAgent] | None = None,
    # ---- legacy kwargs kept for backward compat ----
    **overrides,
) -> Iterator[L3Add | L3Execute | L3Cancel]:
    """Generate a realistic stream of ITCH L3 messages.

    Parameters
    ----------
    book : Orderbook
        The order book instance to operate on.
    cfg : SimulationConfig, optional
        Full configuration.  If ``None`` a default is built (can be
        patched via *overrides*).
    agents : list[BaseAgent], optional
        Pluggable trading agents.
    **overrides
        Any ``SimulationConfig`` field name → value to override.
        ``start_price``, ``spread``, ``seed``, ``sleep_sec``, etc.
    """
    if cfg is None:
        cfg = SimulationConfig(**{
            k: v for k, v in overrides.items()
            if k in SimulationConfig.__dataclass_fields__
        })

    rng = random.Random(cfg.seed)
    next_id = 1
    t = 0
    min_price = max(book.tick_size, cfg.min_price)
    min_tick = book.price_to_tick(min_price)
    mid_price = max(min_price, cfg.start_price)
    anchor_price = mid_price
    momentum = 0.0
    regime = "normal"

    # Ensure we always have agents for order ownership
    if not agents:
        agents = [
            MarketMaker(),
            MarketMaker(spread_ticks=3, size=8),
            NoiseTrader(),
            NoiseTrader(spread_ticks=6, size=5),
        ]

    # ================================================================
    # Day loop
    # ================================================================
    day = 0
    while cfg.num_days is None or day < cfg.num_days:

        # ---- pre‑market seeding ----
        next_id = seed_book(
            book, mid_price, cfg.spread, rng, next_id,
            n_levels=cfg.seed_levels,
            orders_per_level=cfg.seed_orders_per_level,
            validate=cfg.validate_orders,
            agents=agents,
        )

        for sec in range(cfg.session_seconds):
            # intraday modulation
            activity = intraday_activity_factor(sec, cfg.session_seconds)
            vol_scale = intraday_volatility_factor(sec, cfg.session_seconds)

            # periodic stale‑order purge (agent-driven)
            if sec > 0 and sec % cfg.stale_purge_interval == 0:
                mid_tick = book.price_to_tick(mid_price)
                for msg, t in purge_stale_orders(
                    book, agents, mid_tick, cfg.stale_purge_distance, rng, t,
                ):
                    yield msg

            # regime switch
            if rng.random() < cfg.regime_switch_prob:
                regime = rng.choice(list(cfg.regimes.keys()))

            params = cfg.regimes[regime]
            spread_mult = params["spread_mult"]
            imbalance = params["imbalance"]

            # evolve mid price
            mid_price, momentum, regime = evolve_mid_price(
                rng, mid_price, momentum, cfg.regimes, regime,
                regime_switch_prob=cfg.regime_switch_prob,
                anchor_price=anchor_price,
                mean_reversion=cfg.mean_reversion,
                min_price=min_price,
                volatility_scale=vol_scale,
            )
            mid_price = max(min_price, mid_price)

            # ---- agent orders ----
            if agents:
                mid_tick = book.price_to_tick(mid_price)
                ctx = AgentContext(
                    t=t,
                    mid_price=mid_price,
                    mid_tick=mid_tick,
                    best_bid=book.best_bid(),
                    best_ask=book.best_ask(),
                    momentum=momentum,
                )
                for agent in agents:
                    agent_orders, next_id = agent.generate_orders(
                        book, ctx, next_id,
                        validate_orders=cfg.validate_orders,
                    )
                    for order in agent_orders:
                        for msg, t in emit_order(book, order, t):
                            yield msg
                        # track ownership: this agent placed it
                        if order.id in book.order_index:
                            agent.on_order_placed(order.id)

            # ---- random order flow ----
            n_orders = max(1, int(cfg.orders_per_tick * activity))
            for _ in range(n_orders):
                # side bias
                side_bias = 0.5 + imbalance + (0.05 if momentum > 0 else -0.05)
                side_bias = min(max(side_bias, 0.05), 0.95)
                side = Side.BID if rng.random() < side_bias else Side.ASK

                eff_market_ratio = max(
                    0.01,
                    min(0.9, cfg.market_ratio * params["market_ratio"] / 0.15),
                )
                is_market = rng.random() < eff_market_ratio

                # cancellations (owner-initiated)
                if rng.random() < cfg.cancel_ratio:
                    mid_tick = book.price_to_tick(mid_price)
                    msg, t = try_cancel_owned(book, agents, mid_tick, rng, t)
                    if msg:
                        yield msg

                # build order
                order = make_random_order(
                    rng, next_id, side, is_market,
                    mid_price, cfg.spread, spread_mult,
                    min_price, min_tick, book, t,
                    validate=cfg.validate_orders,
                )
                next_id += 1

                # replenish if limit
                if not is_market and cfg.replenish:
                    owner = rng.choice(agents)
                    for msg, t, next_id in replenish_book(
                        book, mid_price, cfg.spread, spread_mult,
                        next_id, min_tick, rng, t,
                        validate=cfg.validate_orders,
                        owner_agent=owner,
                    ):
                        yield msg

                # submit order
                for msg, t in emit_order(book, order, t):
                    yield msg
                # assign ownership to a random agent if order rested
                if order.id in book.order_index:
                    rng.choice(agents).on_order_placed(order.id)

            if cfg.sleep_sec > 0:
                time.sleep(cfg.sleep_sec)

        # ============ End of trading day ============
        day += 1
        if cfg.num_days is not None and day >= cfg.num_days:
            return

        # overnight
        clear_book(book)
        for a in agents:
            a.clear()
        mid_price = overnight_gap(rng, mid_price, cfg.overnight_gap_sigma)
        mid_price = max(min_price, mid_price)
        anchor_price = daily_drift(rng, anchor_price, cfg.daily_drift_sigma)
        anchor_price = max(min_price, anchor_price)
        momentum *= 0.3
        regime = "normal"


# ------------------------------------------------------------------
# Batch wrapper
# ------------------------------------------------------------------

def stream_fake_market_batch(
    book: Orderbook,
    batch_size: int = 100,
    **kwargs,
) -> Iterator[list[L3Add | L3Execute | L3Cancel]]:
    """Yield L3 messages in batches for higher throughput."""
    gen = stream_fake_market(book, **kwargs)
    while True:
        batch: list[L3Add | L3Execute | L3Cancel] = []
        for _ in range(batch_size):
            batch.append(next(gen))
        yield batch
