"""Simulation configuration — all tunables in one place."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from core.config import VALIDATE_ORDERS


# ---------------------------------------------------------------------------
# Regime definitions (sigma / jump / spread / market order ratio / imbalance)
# ---------------------------------------------------------------------------

RegimeParams = dict[str, float]

DEFAULT_REGIMES: dict[str, RegimeParams] = {
    "calm": {
        "sigma": 0.002,
        "jump_prob": 0.0005,
        "jump_sigma": 0.01,
        "spread_mult": 0.7,
        "market_ratio": 0.08,
        "imbalance": 0.01,
    },
    "normal": {
        "sigma": 0.005,
        "jump_prob": 0.002,
        "jump_sigma": 0.03,
        "spread_mult": 1.0,
        "market_ratio": 0.15,
        "imbalance": 0.0,
    },
    "stress": {
        "sigma": 0.02,
        "jump_prob": 0.008,
        "jump_sigma": 0.08,
        "spread_mult": 1.6,
        "market_ratio": 0.30,
        "imbalance": -0.03,
    },
}


# ---------------------------------------------------------------------------
# Main config dataclass
# ---------------------------------------------------------------------------

@dataclass
class SimulationConfig:
    """All simulation parameters grouped in one object.

    Pass this to ``stream_fake_market`` (or build one from CLI flags later).
    """

    # Price
    start_price: float = 10.0
    spread: float = 0.10
    min_price: float = 1.0
    mean_reversion: float = 0.001

    # Order flow
    orders_per_tick: int = 12
    market_ratio: float = 0.12
    cancel_ratio: float = 0.30

    # Randomness
    seed: int = 42

    # Book management
    replenish: bool = True
    stale_purge_distance: int = 120
    stale_purge_interval: int = 20
    seed_levels: int = 20
    seed_orders_per_level: int = 4

    # Multi‑day
    num_days: int | None = None
    session_seconds: int = 23_400
    overnight_gap_sigma: float = 0.010
    daily_drift_sigma: float = 0.006

    # Regime switching
    regime_switch_prob: float = 0.008
    regimes: dict[str, RegimeParams] = field(default_factory=lambda: dict(DEFAULT_REGIMES))

    # Performance
    sleep_sec: float = 0.0
    validate_orders: bool = VALIDATE_ORDERS
