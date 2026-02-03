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

    mid_price *= max(0.01, 1.0 + shock + jump)
    mid_price = max(0.01, mid_price)
    return mid_price, momentum, regime
