"""Shared stochastic mid-price evolution with intraday patterns."""

from __future__ import annotations

import math
import random


# ---------------------------------------------------------------------------
# Intraday modulation helpers
# ---------------------------------------------------------------------------

def intraday_activity_factor(
    seconds_into_session: float,
    session_duration: float,
) -> float:
    """U-shaped intraday activity curve (high at open/close, low midday).

    Models the well-known volume smile:
      - Opening rush  (~first 20 min → boost)
      - Midday lull   (reduced activity)
      - Closing rush  (~last 15 min → boost)

    Returns a multiplier in ~[0.3, 2.5].
    """
    t = seconds_into_session / max(1.0, session_duration)
    u = 4.0 * (t - 0.5) ** 2           # 0 at midday, 1 at edges
    open_boost = max(0.0, 1.0 - 5.0 * t) * 0.5
    close_rush = max(0.0, (t - 0.85) / 0.15) * 0.3
    return max(0.3, min(2.5, 0.4 + 1.2 * u + open_boost + close_rush))


def intraday_volatility_factor(
    seconds_into_session: float,
    session_duration: float,
) -> float:
    """Volatility U-shape — higher at open/close, lower midday.

    Returns a multiplier in ~[0.4, 2.0].
    """
    t = seconds_into_session / max(1.0, session_duration)
    u = 4.0 * (t - 0.5) ** 2
    factor = 0.6 + 0.6 * u
    if t < 0.05:
        factor += 0.4
    return max(0.4, min(2.0, factor))


def overnight_gap(
    rng: random.Random,
    mid_price: float,
    gap_sigma: float = 0.012,
) -> float:
    """Simulate overnight price gap between trading sessions.

    Models the jump that occurs between close and next open due to
    overnight news, pre-market activity, etc.
    Typical stocks: ±0.5 – 2 % gap.  gap_sigma=0.012 → 95 % within ±2.4 %.

    Returns the new mid price after the gap.
    """
    return mid_price * (1.0 + rng.gauss(0.0, gap_sigma))


def daily_drift(
    rng: random.Random,
    anchor_price: float,
    drift_sigma: float = 0.008,
) -> float:
    """Shift the long-term anchor slightly each day (random walk of the fair value).

    This avoids the price being mean-reverting to the *same* level
    forever.  Over N days the anchor wanders like sqrt(N) * drift_sigma.
    """
    return anchor_price * (1.0 + rng.gauss(0.0, drift_sigma))


# ---------------------------------------------------------------------------
# Core price evolution
# ---------------------------------------------------------------------------

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
    volatility_scale: float = 1.0,
) -> tuple[float, float, str]:
    """Evolve mid price using stochastic process with regime switching.

    Args:
        volatility_scale: Intraday multiplier applied to sigma & jump_sigma.
            Typically comes from ``intraday_volatility_factor()``.
    """
    if rng.random() < regime_switch_prob:
        regime = rng.choice(list(regimes.keys()))

    params = regimes[regime]
    sigma = params["sigma"] * volatility_scale
    shock = rng.gauss(0.0, sigma)
    momentum = 0.95 * momentum + shock
    jump = 0.0
    if rng.random() < params["jump_prob"]:
        jump = rng.gauss(0.0, params["jump_sigma"] * volatility_scale)

    drift = 0.0
    if anchor_price is not None and anchor_price > 0:
        drift = mean_reversion * (anchor_price - mid_price) / anchor_price

    mid_price *= max(0.01, 1.0 + shock + jump + drift)
    mid_price = max(min_price, mid_price)
    return mid_price, momentum, regime
