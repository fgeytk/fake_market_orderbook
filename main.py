from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, Deque
import heapq


class Side(str, Enum):
    BID = "BID"
    ASK = "ASK"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


@dataclass(slots=True)
class Order:
    id: int
    side: Side
    type: OrderType
    quantity: int
    price: Optional[float] = None
    timestamp: int = 0

    def __post_init__(self) -> None:
        # validations
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
            if self.price is None or not isinstance(self.price, (int, float)) or self.price <= 0:
                raise ValueError("LIMIT order needs a positive price")
        else:  # MARKET
            if self.price is not None:
                raise ValueError("MARKET order must not have a price")

    def __repr__(self) -> str:
        return (
            f"Order(id={self.id}, side={self.side.value}, type={self.type.value}, "
            f"qty={self.quantity}, price={self.price}, ts={self.timestamp})"
        )


@dataclass(slots=True)
class Trade:
    maker_id: int
    price: float
    quantity: int


@dataclass(slots=True)
class Orderbook:
    bids: dict[float, Deque[Order]] = field(default_factory=dict)  # price -> FIFO queue
    asks: dict[float, Deque[Order]] = field(default_factory=dict)
    bid_heap: list[float] = field(default_factory=list)  # store -price
    ask_heap: list[float] = field(default_factory=list)  # store +price

    def _clean_top(self, side: Side) -> None:
        if side == Side.BID:
            heap = self.bid_heap
            levels = self.bids
            sign = -1.0
        else:
            heap = self.ask_heap
            levels = self.asks
            sign = +1.0

        while heap:
            price = sign * heap[0]
            q = levels.get(price)
            if not q:  # absent ou deque vide
                heapq.heappop(heap)
                continue
            break

    def best_bid(self) -> tuple[float, int] | None:
        self._clean_top(Side.BID)
        if not self.bid_heap:
            return None
        price = -self.bid_heap[0]
        qty = sum(o.quantity for o in self.bids[price])
        return price, qty

    def best_ask(self) -> tuple[float, int] | None:
        self._clean_top(Side.ASK)
        if not self.ask_heap:
            return None
        price = self.ask_heap[0]
        qty = sum(o.quantity for o in self.asks[price])
        return price, qty

    def add_limit(self, order: Order) -> None:
        if order.type != OrderType.LIMIT:
            raise ValueError("add_limit expects a LIMIT order")

        price = float(order.price)

        if order.side == Side.BID:
            if price not in self.bids:
                self.bids[price] = deque()
                heapq.heappush(self.bid_heap, -price)
            self.bids[price].append(order)
        else:
            if price not in self.asks:
                self.asks[price] = deque()
                heapq.heappush(self.ask_heap, price)
            self.asks[price].append(order)

    def _match_against_book(
        self,
        incoming_side: Side,
        remaining_qty: int,
        limit_price: float | None = None,
    ) -> tuple[list[Trade], int]:
        trades: list[Trade] = []

        if incoming_side == Side.BID:
            book_side = Side.ASK
            heap = self.ask_heap
            levels = self.asks
            price_sign = 1.0
        else:
            book_side = Side.BID
            heap = self.bid_heap
            levels = self.bids
            price_sign = -1.0

        while remaining_qty > 0:
            self._clean_top(book_side)
            if not heap:
                break

            best_price = price_sign * heap[0]
            if limit_price is not None:
                if incoming_side == Side.BID and best_price > limit_price:
                    break
                if incoming_side == Side.ASK and best_price < limit_price:
                    break
            queue = levels[best_price]

            while queue and remaining_qty > 0:
                top_order = queue[0]
                trade_qty = min(remaining_qty, top_order.quantity)

                trades.append(Trade(top_order.id, best_price, trade_qty))

                remaining_qty -= trade_qty
                top_order.quantity -= trade_qty

                if top_order.quantity == 0:
                    queue.popleft()

            if not queue:
                del levels[best_price]
                heapq.heappop(heap)

        return trades, remaining_qty

    def matchtrade(self, order: Order) -> list[Trade]:
        if order.type != OrderType.MARKET:
            raise ValueError("matchtrade expects a MARKET order")

        trades, _ = self._match_against_book(order.side, order.quantity)
        return trades

    def add_order(self, order: Order) -> list[Trade]:
        if order.type == OrderType.LIMIT:
            trades, remaining_qty = self._match_against_book(
                order.side,
                order.quantity,
                float(order.price),
            )
            if remaining_qty > 0:
                order.quantity = remaining_qty
                self.add_limit(order)
            return trades
        else:  # MARKET
            return self.matchtrade(order)

if __name__ == "__main__":
    from market_stream import stream_fake_market

    book = Orderbook()

    for order, trades in stream_fake_market(book):
        print(f"New order: {order}")
        for trade in trades:
            print(f"  Trade executed: {trade}")
        best_bid = book.best_bid()
        best_ask = book.best_ask()
        print(f"  Best Bid: {best_bid}, Best Ask: {best_ask}\n")
