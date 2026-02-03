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
    maker_id: int
    price_tick: int
    quantity: int


@dataclass(slots=True)
class Orderbook:
    tick_size: float = 0.01
    debug: bool = False
    bids: dict[int, Deque[Order]] = field(default_factory=dict)  # price_tick -> FIFO queue
    asks: dict[int, Deque[Order]] = field(default_factory=dict)
    bid_heap: list[int] = field(default_factory=list)  # store -price_tick
    ask_heap: list[int] = field(default_factory=list)  # store +price_tick
    order_index: dict[int, tuple[Side, int]] = field(default_factory=dict)  # id -> (side, price_tick)

    def price_to_tick(self, price: float) -> int:
        if price <= 0:
            raise ValueError("price must be > 0")
        return int(round(price / self.tick_size))

    def tick_to_price(self, tick: int) -> float:
        return tick * self.tick_size

    def _clean_top(self, side: Side) -> None:
        if side == Side.BID:
            heap = self.bid_heap
            levels = self.bids
            sign = -1
        else:
            heap = self.ask_heap
            levels = self.asks
            sign = 1

        while heap:
            price_tick = sign * heap[0]
            q = levels.get(price_tick)
            if not q:  # absent or empty deque
                heapq.heappop(heap)
                continue
            break

    def best_bid(self) -> tuple[int, int] | None:
        self._clean_top(Side.BID)
        if not self.bid_heap:
            return None
        price_tick = -self.bid_heap[0]
        qty = sum(o.quantity for o in self.bids[price_tick])
        return price_tick, qty

    def best_ask(self) -> tuple[int, int] | None:
        self._clean_top(Side.ASK)
        if not self.ask_heap:
            return None
        price_tick = self.ask_heap[0]
        qty = sum(o.quantity for o in self.asks[price_tick])
        return price_tick, qty

    def _assert_invariants(self) -> None:
        if not self.debug:
            return

        best_bid = self.best_bid()
        best_ask = self.best_ask()
        if best_bid and best_ask:
            assert best_bid[0] < best_ask[0], "Crossed book detected"

        if self.bid_heap:
            top_tick = -self.bid_heap[0]
            assert top_tick in self.bids and self.bids[top_tick], "Bid heap desync"

        if self.ask_heap:
            top_tick = self.ask_heap[0]
            assert top_tick in self.asks and self.asks[top_tick], "Ask heap desync"

    def add_limit(self, order: Order) -> None:
        if order.type != OrderType.LIMIT:
            raise ValueError("add_limit expects a LIMIT order")
        if order.price_tick is None:
            raise ValueError("LIMIT order needs price_tick")

        price_tick = int(order.price_tick)

        if order.side == Side.BID:
            if price_tick not in self.bids:
                self.bids[price_tick] = deque()
                heapq.heappush(self.bid_heap, -price_tick)
            self.bids[price_tick].append(order)
        else:
            if price_tick not in self.asks:
                self.asks[price_tick] = deque()
                heapq.heappush(self.ask_heap, price_tick)
            self.asks[price_tick].append(order)

        self.order_index[order.id] = (order.side, price_tick)
        self._assert_invariants()

    def _match_against_book(
        self,
        incoming_side: Side,
        remaining_qty: int,
        limit_tick: int | None = None,
    ) -> tuple[list[Trade], int]:
        trades: list[Trade] = []

        if incoming_side == Side.BID:
            book_side = Side.ASK
            heap = self.ask_heap
            levels = self.asks
            price_sign = 1
        else:
            book_side = Side.BID
            heap = self.bid_heap
            levels = self.bids
            price_sign = -1

        while remaining_qty > 0:
            self._clean_top(book_side)
            if not heap:
                break

            best_tick = price_sign * heap[0]
            if limit_tick is not None:
                if incoming_side == Side.BID and best_tick > limit_tick:
                    break
                if incoming_side == Side.ASK and best_tick < limit_tick:
                    break

            queue = levels[best_tick]
            while queue and remaining_qty > 0:
                top_order = queue[0]
                trade_qty = min(remaining_qty, top_order.quantity)

                trades.append(Trade(top_order.id, best_tick, trade_qty))

                remaining_qty -= trade_qty
                top_order.quantity -= trade_qty

                if top_order.quantity == 0:
                    queue.popleft()
                    self.order_index.pop(top_order.id, None)

            if not queue:
                del levels[best_tick]

        self._assert_invariants()
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
                order.price_tick,
            )
            if remaining_qty > 0:
                order.quantity = remaining_qty
                self.add_limit(order)
            return trades
        return self.matchtrade(order)

    def cancel_at_price(self, side: Side, price_tick: int) -> Order | None:
        levels = self.bids if side == Side.BID else self.asks
        queue = levels.get(price_tick)
        if not queue:
            return None
        order = queue.popleft()
        self.order_index.pop(order.id, None)
        if not queue:
            del levels[price_tick]
        self._assert_invariants()
        return order

    def cancel_by_id(self, order_id: int) -> bool:
        info = self.order_index.get(order_id)
        if not info:
            return False
        side, price_tick = info
        levels = self.bids if side == Side.BID else self.asks
        queue = levels.get(price_tick)
        if not queue:
            self.order_index.pop(order_id, None)
            return False

        new_queue = deque()
        removed = False
        while queue:
            order = queue.popleft()
            if order.id == order_id and not removed:
                removed = True
                continue
            new_queue.append(order)

        if new_queue:
            levels[price_tick] = new_queue
        else:
            levels.pop(price_tick, None)

        if removed:
            self.order_index.pop(order_id, None)
        self._assert_invariants()
        return removed

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
