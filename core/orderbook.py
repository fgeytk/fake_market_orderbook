"""Orderbook implementation with tick-based pricing."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Deque
import heapq

from core.models import Order, Trade, Side, OrderType
from core.config import TICK_SIZE, DEBUG


@dataclass(slots=True)
class Orderbook:
    """
    A limit orderbook with tick-based pricing and price-time priority matching.
    
    Uses heaps for O(1) best price retrieval and FIFO queues for price-time priority.
    """
    tick_size: float = TICK_SIZE
    debug: bool = DEBUG
    bids: dict[int, Deque[Order]] = field(default_factory=dict)  # price_tick -> FIFO queue
    asks: dict[int, Deque[Order]] = field(default_factory=dict)
    bid_sizes: dict[int, int] = field(default_factory=dict)  # price_tick -> total quantity
    ask_sizes: dict[int, int] = field(default_factory=dict)
    bid_heap: list[int] = field(default_factory=list)  # store -price_tick
    ask_heap: list[int] = field(default_factory=list)  # store +price_tick
    order_index: dict[int, tuple[Side, int]] = field(default_factory=dict)  # id -> (side, price_tick)

    def price_to_tick(self, price: float) -> int:
        """Convert a float price to an integer tick."""
        if price <= 0:
            raise ValueError("price must be > 0")
        return int(round(price / self.tick_size))

    def tick_to_price(self, tick: int) -> float:
        """Convert an integer tick to a float price."""
        return tick * self.tick_size

    def _clean_top(self, side: Side) -> None:
        """Remove empty price levels from the top of the heap."""
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
        """Return (price_tick, total_quantity) for the best bid, or None."""
        self._clean_top(Side.BID)
        if not self.bid_heap:
            return None
        price_tick = -self.bid_heap[0]
        return price_tick, self.bid_sizes.get(price_tick, 0)

    def best_ask(self) -> tuple[int, int] | None:
        """Return (price_tick, total_quantity) for the best ask, or None."""
        self._clean_top(Side.ASK)
        if not self.ask_heap:
            return None
        price_tick = self.ask_heap[0]
        return price_tick, self.ask_sizes.get(price_tick, 0)

    def _assert_invariants(self) -> None:
        """Check orderbook invariants (no crossed book, heap sync)."""
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
        """Add a limit order to the orderbook (non-matching)."""
        if order.type != OrderType.LIMIT:
            raise ValueError("add_limit expects a LIMIT order")
        if order.price_tick is None:
            raise ValueError("LIMIT order needs price_tick")

        price_tick = int(order.price_tick)

        if order.side == Side.BID:
            if price_tick not in self.bids:
                self.bids[price_tick] = deque()
                self.bid_sizes[price_tick] = 0
                heapq.heappush(self.bid_heap, -price_tick)
            self.bids[price_tick].append(order)
            self.bid_sizes[price_tick] += order.quantity
        else:
            if price_tick not in self.asks:
                self.asks[price_tick] = deque()
                self.ask_sizes[price_tick] = 0
                heapq.heappush(self.ask_heap, price_tick)
            self.asks[price_tick].append(order)
            self.ask_sizes[price_tick] += order.quantity

        self.order_index[order.id] = (order.side, price_tick)
        self._assert_invariants()

    def _match_against_book(
        self,
        incoming_side: Side,
        remaining_qty: int,
        limit_tick: int | None = None,
    ) -> tuple[list[Trade], int]:
        """
        Match an incoming order against the book.
        
        Returns (trades, remaining_quantity).
        """
        trades: list[Trade] = []

        if incoming_side == Side.BID:
            book_side = Side.ASK
            heap = self.ask_heap
            levels = self.asks
            sizes = self.ask_sizes
            price_sign = 1
        else:
            book_side = Side.BID
            heap = self.bid_heap
            levels = self.bids
            sizes = self.bid_sizes
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
                sizes[best_tick] -= trade_qty

                if top_order.quantity == 0:
                    queue.popleft()
                    self.order_index.pop(top_order.id, None)

            if not queue:
                del levels[best_tick]
                sizes.pop(best_tick, None)

        self._assert_invariants()
        return trades, remaining_qty

    def matchtrade(self, order: Order) -> list[Trade]:
        """Match a market order against the book."""
        if order.type != OrderType.MARKET:
            raise ValueError("matchtrade expects a MARKET order")

        trades, _ = self._match_against_book(order.side, order.quantity)
        return trades

    def add_order(self, order: Order) -> list[Trade]:
        """
        Add an order to the book.
        
        LIMIT orders match aggressively, then post remainder.
        MARKET orders match completely or are lost.
        
        Returns list of trades executed.
        """
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
        """Cancel the first order at a given price level."""
        levels = self.bids if side == Side.BID else self.asks
        sizes = self.bid_sizes if side == Side.BID else self.ask_sizes
        queue = levels.get(price_tick)
        if not queue:
            return None
        order = queue.popleft()
        sizes[price_tick] = max(0, sizes.get(price_tick, 0) - order.quantity)
        self.order_index.pop(order.id, None)
        if not queue:
            del levels[price_tick]
            sizes.pop(price_tick, None)
        self._assert_invariants()
        return order

    def cancel_by_id(self, order_id: int) -> bool:
        """Cancel a specific order by ID."""
        info = self.order_index.get(order_id)
        if not info:
            return False
        side, price_tick = info
        levels = self.bids if side == Side.BID else self.asks
        sizes = self.bid_sizes if side == Side.BID else self.ask_sizes
        queue = levels.get(price_tick)
        if not queue:
            self.order_index.pop(order_id, None)
            return False

        new_queue = deque()
        removed = False
        removed_qty = 0
        while queue:
            order = queue.popleft()
            if order.id == order_id and not removed:
                removed = True
                removed_qty = order.quantity
                continue
            new_queue.append(order)

        if new_queue:
            levels[price_tick] = new_queue
        else:
            levels.pop(price_tick, None)
            sizes.pop(price_tick, None)

        if removed_qty:
            sizes[price_tick] = max(0, sizes.get(price_tick, 0) - removed_qty)

        if removed:
            self.order_index.pop(order_id, None)
        self._assert_invariants()
        return removed
