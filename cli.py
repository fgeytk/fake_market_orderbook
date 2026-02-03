"""Command-line interface for simulation, visualization, and profiling."""

from __future__ import annotations

import cProfile
import io
import pstats
from dataclasses import asdict
from typing import Any

import typer

from core import Orderbook
from simulation import stream_fake_market
from visualization import create_app

app = typer.Typer(add_completion=False)


def _to_primitive(obj: Any) -> Any:
    if hasattr(obj, "__dataclass_fields__"):
        data = asdict(obj)
        return {k: _to_primitive(v) for k, v in data.items()}
    if isinstance(obj, list):
        return [_to_primitive(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_primitive(v) for k, v in obj.items()}
    if hasattr(obj, "value"):
        return obj.value
    return obj


@app.command()
def viz(
    host: str = typer.Option("127.0.0.1", help="Host to bind"),
    port: int = typer.Option(8050, help="Port to bind"),
) -> None:
    """Launch the interactive Dash visualization server."""
    print(f"Starting visualization on http://{host}:{port}")
    app_dash = create_app()
    app_dash.run(host=host, port=port, debug=False)


@app.command()
def stream(
    steps: int = typer.Option(20, help="Number of events to emit"),
    sleep_sec: float = typer.Option(0.0, help="Sleep between ticks"),
) -> None:
    """Run the market stream for a fixed number of events."""
    book = Orderbook()
    generator = stream_fake_market(book, sleep_sec=sleep_sec)

    for i in range(steps):
        event, trades = next(generator)
        print({
            "index": i,
            "event": _to_primitive(event),
            "trades": _to_primitive(trades),
        })


@app.command()
def profile(
    steps: int = typer.Option(2000, help="Number of events to profile"),
    sleep_sec: float = typer.Option(0.0, help="Sleep between ticks"),
) -> None:
    """Profile the market stream and print top hotspots."""
    book = Orderbook()
    generator = stream_fake_market(book, sleep_sec=sleep_sec)

    profiler = cProfile.Profile()
    profiler.enable()
    for _ in range(steps):
        next(generator)
    profiler.disable()

    buf = io.StringIO()
    stats = pstats.Stats(profiler, stream=buf).sort_stats("tottime")
    stats.print_stats(25)

    print(buf.getvalue())


if __name__ == "__main__":
    app()
