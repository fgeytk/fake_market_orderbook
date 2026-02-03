"""
Orderbook Trading Simulation
=============================

A realistic limit orderbook implementation with:
- Tick-based pricing to avoid float precision issues
- Price-time priority matching engine
- Regime-based market simulation (calm/normal/stress)
- Interactive real-time visualization

Project Structure:
- core/: Orderbook engine and data models
- simulation/: Market data generation and trading agents
- visualization/: Interactive Dash/Plotly UI

Usage:
    # Run visualization server:
    python main.py

    # Or run from individual modules:
    python -m visualization.orderbook_viz
    python -m simulation.market_stream
"""

from __future__ import annotations

from core import Orderbook
from simulation import stream_fake_market
from visualization import create_app


def run_visualization() -> None:
    """Launch the interactive orderbook visualization."""
    print("Starting orderbook visualization...")
    print("Open http://127.0.0.1:8050 in your browser")
    app = create_app()
    app.run(debug=False)


def run_simple_test() -> None:
    """Run a simple test of the orderbook and market stream."""
    from dataclasses import asdict
    
    print("Running simple orderbook test...")
    book = Orderbook()
    
    for i, (event, trades) in enumerate(stream_fake_market(book)):
        if i >= 20:  # Just show first 20 events
            break
        print(f"\nEvent {i}:")
        if hasattr(event, '__dataclass_fields__'):
            print(f"  {asdict(event)}")
        else:
            print(f"  {event}")
        for trade in trades:
            print(f"  Trade: {asdict(trade)}")
        best_bid = book.best_bid()
        best_ask = book.best_ask()
        if best_bid:
            print(f"  Best Bid: {book.tick_to_price(best_bid[0]):.2f} x {best_bid[1]}")
        if best_ask:
            print(f"  Best Ask: {book.tick_to_price(best_ask[0]):.2f} x {best_ask[1]}")


def main() -> None:
    """Main entry point."""
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        run_simple_test()
    else:
        run_visualization()


if __name__ == "__main__":
    main()
