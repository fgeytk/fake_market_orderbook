"""
viz_dash = version refactorisée qui utilise 
core/simulation + agents + batch + caches bid_sizes/ask_sizes (plus rapide et plus propre)
"""

from __future__ import annotations

import sys
import math
import heapq
from pathlib import Path
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

if __package__ in (None, ""):
    project_root = Path(__file__).resolve().parents[1]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from core import Orderbook
from simulation import stream_fake_market_batch, MarketMaker, MomentumTrader, MeanReversionTrader, NoiseTrader


def _depth_snapshot(
    book: Orderbook, depth_levels: int = 10
) -> tuple[list[int], list[int], list[int], list[int]]:
    """heaps for O(1) retrieval of top depth levels."""
    bid_levels = heapq.nlargest(depth_levels, book.bid_sizes.items(), key=lambda x: x[0])
    ask_levels = heapq.nsmallest(depth_levels, book.ask_sizes.items(), key=lambda x: x[0])

    bid_prices = [p for p, _ in bid_levels]
    bid_sizes = [size for _, size in bid_levels]

    ask_prices = [p for p, _ in ask_levels]
    ask_sizes = [size for _, size in ask_levels]

    return bid_prices, bid_sizes, ask_prices, ask_sizes


def _build_figure(book: Orderbook, depth_levels: int = 10) -> go.Figure:
    """Build a Plotly figure showing orderbook depth with log compression."""
    bid_prices, bid_sizes, ask_prices, ask_sizes = _depth_snapshot(book, depth_levels)
    bid_prices_float = [book.tick_to_price(p) for p in bid_prices]
    ask_prices_float = [book.tick_to_price(p) for p in ask_prices]

    # Apply log compression to sizes for better visualization
    bid_sizes_log = [math.log1p(s) for s in bid_sizes]
    ask_sizes_log = [math.log1p(s) for s in ask_sizes]

    fig = go.Figure()
    # Bids on the right (positive x)
    if bid_prices:
        fig.add_trace(
            go.Bar(
                x=bid_sizes_log,
                y=bid_prices_float,
                orientation="h",
                name="BID",
                marker_color="#2ecc71",
                hovertemplate="Price: %{y:.2f}<br>Size (log): %{x:.2f}<extra></extra>",
            )
        )
    # Asks on the left (negative x)
    if ask_prices:
        fig.add_trace(
            go.Bar(
                x=[-s for s in ask_sizes_log],
                y=ask_prices_float,
                orientation="h",
                name="ASK",
                marker_color="#e74c3c",
                hovertemplate="Price: %{y:.2f}<br>Size (log): %{x:.2f}<extra></extra>",
            )
        )

    best_bid = book.best_bid()
    best_ask = book.best_ask()
    title = "Orderbook Depth"
    if best_bid or best_ask:
        best_bid_str = (
            f"({book.tick_to_price(best_bid[0]):.2f}, {best_bid[1]})" if best_bid else "None"
        )
        best_ask_str = (
            f"({book.tick_to_price(best_ask[0]):.2f}, {best_ask[1]})" if best_ask else "None"
        )
        title = f"Orderbook Depth | Best Bid: {best_bid_str} | Best Ask: {best_ask_str}"

    # Use log-compressed max for symmetric range (stable chart)
    max_depth_log = max([1.0, *bid_sizes_log, *ask_sizes_log])
    # Add 10% padding and round up for stability
    x_limit = math.ceil(max_depth_log * 1.1)

    fig.update_layout(
        title=title,
        barmode="overlay",
        xaxis_title="Depth (log scale)",
        yaxis_title="Price",
        template="plotly_dark",
        height=600,
        xaxis=dict(
            range=[-x_limit, x_limit],
            zeroline=True,
            zerolinecolor="#ffffff",
            zerolinewidth=2,
            fixedrange=True,
        ),
        yaxis=dict(fixedrange=False),
    )
    return fig


def create_app() -> dash.Dash:
    """Create and configure the Dash application."""
    app = dash.Dash(__name__)

    book = Orderbook()
    agents = [
        MarketMaker(),
        MomentumTrader(),
        MeanReversionTrader(ref_price=10.0),
        NoiseTrader(),
    ]
    generator = stream_fake_market_batch(
        book,
        batch_size=50,
        sleep_sec=0.0,
        validate_orders=False,
        agents=agents,
    )

    app.layout = html.Div(
        style={"padding": "12px"},
        children=[
            html.H2("Interactive Orderbook"),
            dcc.Graph(id="orderbook-graph"),
            dcc.Interval(id="tick", interval=250, n_intervals=0),
        ],
    )

    @app.callback(Output("orderbook-graph", "figure"), Input("tick", "n_intervals"))
    def update_graph(_: int) -> go.Figure:
        """Update the orderbook graph at each interval."""
        batch = next(generator)
        # Consume the batch (orders already applied in the generator)
        _ = batch
        return _build_figure(book)

    return app


def main() -> None:
    """Launch the visualization server."""
    app = create_app()
    app.run(debug=False)


if __name__ == "__main__":
    main()
