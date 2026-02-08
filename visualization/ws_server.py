"""WebSocket server streaming ITCH L3 market messages."""

from __future__ import annotations

import asyncio
import msgpack
import threading
import time
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from core import Orderbook
from core.models import L3Add, L3Execute, L3Cancel
from simulation import (
    stream_fake_market_batch,
    MarketMaker,
    MomentumTrader,
    MeanReversionTrader,
    NoiseTrader,
)


def _try_put(queue: asyncio.Queue[bytes], data: bytes) -> None:
    try:
        queue.put_nowait(data)
    except asyncio.QueueFull:
        pass


def _get_orderbook_snapshot(book: Orderbook, seq: int, timestamp: int) -> dict[str, Any]:
    """Extract full depth from orderbook as snapshot."""
    max_levels = None
    
    # Get sorted bids (descending) and asks (ascending)
    bids = []
    if book.bid_heap:
        sorted_bid_ticks = sorted([-tick for tick in book.bid_heap], reverse=True)
        for tick in (sorted_bid_ticks if max_levels is None else sorted_bid_ticks[:max_levels]):
            if tick in book.bids and book.bids[tick]:
                price = book.tick_to_price(tick)
                size = book.bid_sizes.get(tick, 0)
                bids.append([price, size])
    
    asks = []
    if book.ask_heap:
        sorted_ask_ticks = sorted(book.ask_heap)
        for tick in (sorted_ask_ticks if max_levels is None else sorted_ask_ticks[:max_levels]):
            if tick in book.asks and book.asks[tick]:
                price = book.tick_to_price(tick)
                size = book.ask_sizes.get(tick, 0)
                asks.append([price, size])
    
    return {
        "ts": timestamp,
        "seq": seq,
        "bids": bids,
        "asks": asks,
    }


def _producer(
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue[bytes],
    stop_event: threading.Event,
    batch_size: int,
    target_fps: int,
) -> None:
    book = Orderbook()
    agents = [
        MarketMaker(),
        MomentumTrader(),
        MeanReversionTrader(ref_price=10.0),
        NoiseTrader(),
    ]
    generator = stream_fake_market_batch(
        book,
        batch_size=batch_size,
        sleep_sec=0.0,
        validate_orders=False,
        agents=agents,
    )

    interval = 1.0 / max(1, target_fps)
    next_ts = time.perf_counter()
    seq = 0

    while not stop_event.is_set():
        itch_batch = next(generator)
        seq += len(itch_batch)
        
        # Get snapshot after processing batch
        timestamp = time.time_ns()
        snapshot = _get_orderbook_snapshot(book, seq, timestamp)
        data = msgpack.packb(snapshot, use_bin_type=True)
        loop.call_soon_threadsafe(_try_put, queue, data)

        next_ts += interval
        sleep_for = next_ts - time.perf_counter()
        if sleep_for > 0:
            time.sleep(sleep_for)


def create_ws_app(
    batch_size: int = 10,
    target_fps: int = 20,
) -> FastAPI:
    app = FastAPI()

    # Mount old web UI
    web_dir = Path(__file__).resolve().parent / "web"
    if web_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(web_dir), html=True), name="ui")
    
    # Mount new React frontend
    frontend_dir = Path(__file__).resolve().parent / "frontend" / "dist"
    if frontend_dir.exists():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")

    app.state.clients = set()
    app.state.queue = asyncio.Queue(maxsize=10)
    app.state.stop_event = threading.Event()
    app.state.batch_size = batch_size
    app.state.target_fps = target_fps

    @app.on_event("startup")
    async def _startup() -> None:
        app.state.loop = asyncio.get_running_loop()
        app.state.broadcast_task = asyncio.create_task(_broadcast_loop(app))
        app.state.producer = threading.Thread(
            target=_producer,
            args=(
                app.state.loop,
                app.state.queue,
                app.state.stop_event,
                app.state.batch_size,
                app.state.target_fps,
            ),
            daemon=True,
        )
        app.state.producer.start()

    @app.on_event("shutdown")
    async def _shutdown() -> None:
        app.state.stop_event.set()
        if hasattr(app.state, "broadcast_task"):
            app.state.broadcast_task.cancel()
        producer = getattr(app.state, "producer", None)
        if producer and producer.is_alive():
            producer.join(timeout=1.0)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/")
    async def root() -> dict[str, str]:
        return {"status": "ok", "service": "ITCH L3 Feed", "ws": "/ws"}

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        app.state.clients.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except WebSocketDisconnect:
            pass
        finally:
            app.state.clients.discard(websocket)

    return app


async def _broadcast_loop(app: FastAPI) -> None:
    queue: asyncio.Queue[bytes] = app.state.queue
    while True:
        data = await queue.get()
        if not app.state.clients:
            continue
        dead: list[WebSocket] = []
        for ws in list(app.state.clients):
            try:
                await ws.send_bytes(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            app.state.clients.discard(ws)


# Create global app instance
app = create_ws_app()
