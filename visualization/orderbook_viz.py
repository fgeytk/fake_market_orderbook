"""Real-time interactive orderbook depth visualization using Dash."""

from __future__ import annotations

import math
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

from core import Orderbook
from simulation import stream_fake_market


def _depth_snapshot(
    book: Orderbook, depth_levels: int = 10
) -> tuple[list[int], list[int], list[int], list[int]]:
    """Extract the top N price levels from bids and asks."""
    bids = sorted(book.bids.items(), key=lambda x: x[0], reverse=True)[:depth_levels]
    asks = sorted(book.asks.items(), key=lambda x: x[0])[:depth_levels]

    bid_prices = [p for p, _ in bids]
    bid_sizes = [sum(o.quantity for o in q) for _, q in bids]

    ask_prices = [p for p, _ in asks]
    ask_sizes = [sum(o.quantity for o in q) for _, q in asks]

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
                hovertemplate="Price: %{y:.2f}<br>Size: " + 
                              "<br>".join([f"{bid_sizes[i]}" for i in range(len(bid_sizes))]) +
                              "<extra></extra>",
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
                hovertemplate="Price: %{y:.2f}<br>Size: " + 
                              "<br>".join([f"{ask_sizes[i]}" for i in range(len(ask_sizes))]) +
                              "<extra></extra>",
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
    generator = stream_fake_market(book, sleep_sec=0.0)

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
        for _ in range(5):
            next(generator)
        return _build_figure(book)

    return app


def main() -> None:
    """Launch the visualization server."""
    app = create_app()
    app.run(debug=False)


if __name__ == "__main__":
    main()
