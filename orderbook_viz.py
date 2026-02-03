from __future__ import annotations

from collections import deque
from typing import Iterable

import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.graph_objects as go

from main import Orderbook
from market_stream import stream_fake_market


def _depth_snapshot(book: Orderbook, depth_levels: int = 10) -> tuple[list[float], list[int], list[float], list[int]]:
    bids = sorted(book.bids.items(), key=lambda x: x[0], reverse=True)[:depth_levels]
    asks = sorted(book.asks.items(), key=lambda x: x[0])[:depth_levels]

    bid_prices = [p for p, _ in bids]
    bid_sizes = [sum(o.quantity for o in q) for _, q in bids]

    ask_prices = [p for p, _ in asks]
    ask_sizes = [sum(o.quantity for o in q) for _, q in asks]

    return bid_prices, bid_sizes, ask_prices, ask_sizes


def _build_figure(book: Orderbook, depth_levels: int = 10) -> go.Figure:
    bid_prices, bid_sizes, ask_prices, ask_sizes = _depth_snapshot(book, depth_levels)

    fig = go.Figure()
    if bid_prices:
        fig.add_trace(
            go.Bar(
                x=bid_sizes,
                y=bid_prices,
                orientation="h",
                name="BID",
                marker_color="#2ecc71",
            )
        )
    if ask_prices:
        fig.add_trace(
            go.Bar(
                x=[-s for s in ask_sizes],
                y=ask_prices,
                orientation="h",
                name="ASK",
                marker_color="#e74c3c",
            )
        )

    best_bid = book.best_bid()
    best_ask = book.best_ask()
    title = "Orderbook Depth"
    if best_bid or best_ask:
        title = f"Orderbook Depth | Best Bid: {best_bid} | Best Ask: {best_ask}"

    fig.update_layout(
        title=title,
        barmode="overlay",
        xaxis_title="Depth (size)",
        yaxis_title="Price",
        template="plotly_dark",
        height=600,
    )
    fig.update_yaxes(autorange=True)
    return fig


def create_app() -> dash.Dash:
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
        for _ in range(5):
            next(generator)
        return _build_figure(book)

    return app


def main() -> None:
    app = create_app()
    app.run(debug=False)


if __name__ == "__main__":
    main()
