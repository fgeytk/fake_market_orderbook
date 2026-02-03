"""Data models for orders, trades, and events."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Side(str, Enum):
    """Order side (BID or ASK)."""
    BID = "BID"
    ASK = "ASK"


class OrderType(str, Enum):
    """Order type (LIMIT or MARKET)."""
    LIMIT = "LIMIT"
    MARKET = "MARKET"


@dataclass(slots=True)
class Order:
    """Represents a single order in the orderbook."""
    id: int
    side: Side
    type: OrderType
    quantity: int
    price_tick: Optional[int] = None
    timestamp: int = 0

    def __post_init__(self) -> None:
        if not isinstance(self.id, int) or self.id < 0:
            raise ValueError("id must be a non-negative integer")

        if not isinstance(self.timestamp, int) or self.timestamp < 0:
            raise ValueError("timestamp must be a non-negative integer")

        if not isinstance(self.quantity, int) or self.quantity <= 0:
            raise ValueError("quantity must be a positive integer")

        if not isinstance(self.side, Side):
            raise ValueError("Invalid order side")

        if not isinstance(self.type, OrderType):
            raise ValueError("Invalid order type")

        if self.type == OrderType.LIMIT:
            if self.price_tick is None or not isinstance(self.price_tick, int) or self.price_tick <= 0:
                raise ValueError("LIMIT order needs a positive price_tick")
        else:  # MARKET
            if self.price_tick is not None:
                raise ValueError("MARKET order must not have a price_tick")

    def __repr__(self) -> str:
        return (
            f"Order(id={self.id}, side={self.side.value}, type={self.type.value}, "
            f"qty={self.quantity}, price_tick={self.price_tick}, ts={self.timestamp})"
        )


@dataclass(slots=True)
class Trade:
    """Represents an executed trade."""
    maker_id: int
    price_tick: int
    quantity: int


@dataclass(slots=True)
class CancelEvent:
    """Represents an order cancellation event."""
    side: Side
    price_tick: int
    order_id: int | None
