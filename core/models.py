"""Data models for orders, trades, and events."""

from __future__ import annotations

from dataclasses import dataclass, field
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
    validate: bool = field(default=True, repr=False)

    def __post_init__(self) -> None:
        if not self.validate:
            return
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


# ITCH L3 Messages
@dataclass(slots=True)
class L3Add:
    """ITCH-like Add Order message."""
    msg_type: str = "ADD"
    timestamp: float = 0.0
    order_id: int = 0
    side: str = ""
    price_tick: int = 0
    price: float = 0.0
    quantity: int = 0


@dataclass(slots=True)
class L3Execute:
    """ITCH-like Execute Order message."""
    msg_type: str = "EXECUTE"
    timestamp: float = 0.0
    maker_id: int = 0
    price_tick: int = 0
    price: float = 0.0
    quantity: int = 0
    aggressor_side: str = ""


@dataclass(slots=True)
class L3Cancel:
    """ITCH-like Cancel Order message."""
    msg_type: str = "CANCEL"
    timestamp: float = 0.0
    order_id: int = 0
    side: str = ""
    price_tick: int = 0
    price: float = 0.0
    cancelled_quantity: int = 0
