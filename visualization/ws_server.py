"""WebSocket server streaming ITCH L3 market messages."""

from __future__ import annotations

import asyncio
import json
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


def _serialize_l3_message(msg: L3Add | L3Execute | L3Cancel) -> dict[str, Any]:
    """Fast serialization for L3 messages without intermediate dict creation."""
    if isinstance(msg, L3Add):
        return {
            "msg_type": msg.msg_type,
            "timestamp": msg.timestamp,
            "order_id": msg.order_id,
            "side": msg.side,
            "price_tick": msg.price_tick,
            "price": msg.price,
            "quantity": msg.quantity,
        }
    elif isinstance(msg, L3Execute):
        return {
            "msg_type": msg.msg_type,
            "timestamp": msg.timestamp,
            "maker_id": msg.maker_id,
            "price_tick": msg.price_tick,
            "price": msg.price,
            "quantity": msg.quantity,
            "aggressor_side": msg.aggressor_side,
        }
    elif isinstance(msg, L3Cancel):
        return {
            "msg_type": msg.msg_type,
            "timestamp": msg.timestamp,
            "order_id": msg.order_id,
            "side": msg.side,
            "price_tick": msg.price_tick,
            "price": msg.price,
            "cancelled_quantity": msg.cancelled_quantity,
        }
    else:
        # Fallback
        return {}


def _try_put(queue: asyncio.Queue[str], data: str) -> None:
    try:
        queue.put_nowait(data)
    except asyncio.QueueFull:
        pass


def _producer(
    loop: asyncio.AbstractEventLoop,
    queue: asyncio.Queue[str],
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

    while not stop_event.is_set():
        itch_batch = next(generator)
        # Fast serialization without intermediate dict creation
        json_batch = [_serialize_l3_message(msg) for msg in itch_batch]
        data = json.dumps(json_batch)
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

    web_dir = Path(__file__).resolve().parent / "web"
    if web_dir.exists():
        app.mount("/ui", StaticFiles(directory=str(web_dir), html=True), name="ui")

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
                await websocket.receive()
        except WebSocketDisconnect:
            pass
        finally:
            app.state.clients.discard(websocket)

    return app


async def _broadcast_loop(app: FastAPI) -> None:
    queue: asyncio.Queue[str] = app.state.queue
    while True:
        data = await queue.get()
        if not app.state.clients:
            continue
        dead: list[WebSocket] = []
        for ws in list(app.state.clients):
            try:
                await ws.send_text(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            app.state.clients.discard(ws)


# Create global app instance
app = create_ws_app()
