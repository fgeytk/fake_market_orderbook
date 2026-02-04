"""Shared stochastic mid-price evolution."""

from __future__ import annotations

import random


def evolve_mid_price(
    rng: random.Random,
    mid_price: float,
    momentum: float,
    regimes: dict[str, dict[str, float]],
    regime: str,
    regime_switch_prob: float = 0.01,
    anchor_price: float | None = None,
    mean_reversion: float = 0.002,
    min_price: float = 0.01,
) -> tuple[float, float, str]:
    """Evolve mid price using the same stochastic process as the market stream."""
    if rng.random() < regime_switch_prob:
        regime = rng.choice(list(regimes.keys()))

    params = regimes[regime]
    shock = rng.gauss(0.0, params["sigma"])
    momentum = 0.95 * momentum + shock
    jump = 0.0
    if rng.random() < params["jump_prob"]:
        jump = rng.gauss(0.0, params["jump_sigma"])

    drift = 0.0
    if anchor_price is not None and anchor_price > 0:
        drift = mean_reversion * (anchor_price - mid_price) / anchor_price

    mid_price *= max(0.01, 1.0 + shock + jump + drift)
    mid_price = max(min_price, mid_price)
    return mid_price, momentum, regime
