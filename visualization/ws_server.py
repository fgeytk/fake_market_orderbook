"""Binary WebSocket server streaming orderbook depth snapshots."""

from __future__ import annotations

import asyncio
import heapq
import threading
import time

from pathlib import Path

import msgpack
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles

from core import Orderbook
from simulation import (
    stream_fake_market_batch,
    MarketMaker,
    MomentumTrader,
    MeanReversionTrader,
    NoiseTrader,
)


def _depth_snapshot(
    book: Orderbook, depth_levels: int
) -> tuple[list[tuple[float, int]], list[tuple[float, int]]]:
    bid_levels = heapq.nlargest(depth_levels, book.bid_sizes.items(), key=lambda x: x[0])
    ask_levels = heapq.nsmallest(depth_levels, book.ask_sizes.items(), key=lambda x: x[0])

    bids = [(book.tick_to_price(p), int(size)) for p, size in bid_levels]
    asks = [(book.tick_to_price(p), int(size)) for p, size in ask_levels]
    return bids, asks


def _build_snapshot_payload(book: Orderbook, depth_levels: int, seq: int) -> dict:
    bids, asks = _depth_snapshot(book, depth_levels)
    return {
        "type": "snapshot",
        "seq": seq,
        "ts": time.time_ns(),
        "bids": bids,
        "asks": asks,
    }


def _pack_snapshot(payload: dict) -> bytes:
    return msgpack.packb(payload, use_bin_type=True)


def _try_put(queue: asyncio.Queue[bytes], data: bytes) -> None:
    try:
        queue.put_nowait(data)
    except asyncio.QueueFull:
        pass


def _producer(
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue[bytes],
    stop_event: threading.Event,
    snapshot_lock: threading.Lock,
    last_snapshot: dict | None,
    depth_levels: int,
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
        _ = next(generator)
        payload = _build_snapshot_payload(book, depth_levels, seq)
        data = _pack_snapshot(payload)
        with snapshot_lock:
            last_snapshot.clear() if last_snapshot is not None else None
            if last_snapshot is not None:
                last_snapshot.update(payload)
        loop.call_soon_threadsafe(_try_put, queue, data)
        seq += 1

        next_ts += interval
        sleep_for = next_ts - time.perf_counter()
        if sleep_for > 0:
            time.sleep(sleep_for)


def create_ws_app(
    depth_levels: int = 50,
    batch_size: int = 200,
    target_fps: int = 60,
) -> FastAPI:
    app = FastAPI()

    web_dir = Path(__file__).resolve().parent / "web"
    if web_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(web_dir), html=True), name="ui")

    app.state.clients = set()
    app.state.queue = asyncio.Queue(maxsize=2)
    app.state.stop_event = threading.Event()
    app.state.snapshot_lock = threading.Lock()
    app.state.last_snapshot = {}
    app.state.depth_levels = depth_levels
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
                app.state.snapshot_lock,
                app.state.last_snapshot,
                app.state.depth_levels,
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
        return {"status": "ok", "ui": "/ui", "ws": "/ws"}

    @app.get("/snapshot")
    async def snapshot() -> dict:
        with app.state.snapshot_lock:
            return dict(app.state.last_snapshot)

    @app.websocket("/ws")
    async def ws_endpoint(websocket: WebSocket) -> None:
        await websocket.accept()
        app.state.clients.add(websocket)
        try:
            while True:
                await websocket.receive()
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
