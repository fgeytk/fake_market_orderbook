# Orderbook Trading Simulation

A realistic limit orderbook implementation with tick-based pricing, regime-based market simulation, and interactive visualization.

## Project Structure

```
IA/
├── core/                      # Core orderbook engine
│   ├── __init__.py
│   ├── config.py             # Configuration constants (TICK_SIZE, DEBUG)
│   ├── models.py             # Data models (Order, Trade, CancelEvent, Side, OrderType)
│   └── orderbook.py          # Orderbook class with matching engine
│
├── simulation/               # Market simulation
│   ├── __init__.py
│   └── market_stream.py      # Realistic market data generator
│
├── visualization/            # Interactive UI
│   ├── __init__.py
│   └── orderbook_viz.py      # Dash/Plotly real-time visualization
│
├── main.py                   # Entry point
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Features

### Core Orderbook Engine
- **Tick-based pricing**: Avoids floating-point precision issues
- **Price-time priority**: FIFO matching within price levels
- **Heap-based structure**: O(1) best price retrieval
- **Order types**: LIMIT and MARKET orders
- **Cancellation APIs**: Cancel by price level or order ID
- **Invariant checks**: Optional debug mode with assertion checks

### Market Simulation
- **Regime switching**: Calm, normal, and stress market conditions
- **Realistic dynamics**:
  - Stochastic volatility with occasional price jumps
  - Momentum and mean reversion
  - Heavy-tailed order size distribution (lognormal)
  - Concentrated liquidity near mid price (exponential)
  - Order clustering at round price levels
- **Observable events**: All orders, cancellations, and trades are visible
- **Automatic replenishment**: Keeps book near mid price

### Visualization
- **Real-time updates**: 250ms refresh rate
- **Log compression**: Handles extreme order sizes
- **Centered display**: Bids on right, asks on left
- **Symmetric axis**: Stable chart with no erratic jumps
- **Interactive**: Zoom, pan, hover for details

## Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

## Usage

### Run Visualization Server

```bash
python main.py
```

Then open http://127.0.0.1:8050 in your browser.

### Run Simple Test

```bash
python main.py test
```

### Use as Library

```python
from core import Orderbook, Order, OrderType, Side
from simulation import stream_fake_market

# Create orderbook
book = Orderbook()

# Generate market events
for event, trades in stream_fake_market(book):
    print(f"Event: {event}")
    for trade in trades:
        print(f"  Trade: {trade}")
    
    # Check best prices
    best_bid = book.best_bid()  # (price_tick, quantity)
    best_ask = book.best_ask()
```

## Configuration

Edit [core/config.py](core/config.py) to change:
- `TICK_SIZE`: Price discretization (default: 0.01)
- `DEBUG`: Enable invariant checks (default: False)

## Architecture

### Data Flow

```
market_stream.py
    ↓ generates
(Order/CancelEvent)
    ↓ processed by
Orderbook.add_order()
    ↓ produces
   Trades
    ↓ consumed by
orderbook_viz.py
```

### Key Classes

- **Order**: Represents a limit or market order
- **Trade**: Represents an executed trade
- **CancelEvent**: Represents an order cancellation
- **Orderbook**: The core matching engine
- **Side**: BID or ASK enum
- **OrderType**: LIMIT or MARKET enum

### Matching Algorithm

1. **LIMIT orders**: Match aggressively up to limit price, then post remainder
2. **MARKET orders**: Match completely or are lost (no partial fills posted)
3. **Price-time priority**: Within each price level, FIFO ordering
4. **No self-matching**: (future enhancement)

## Future Enhancements

- **Trading Agents** (simulation/agents.py):
  - Market makers
  - Momentum traders
  - Mean reversion traders
  - Arbitrageurs
  - Noise traders

- **Position Tracking**:
  - P&L calculation
  - Risk metrics
  - Capital constraints

- **Advanced Features**:
  - Self-trade prevention
  - Order modification (cancel-replace)
  - Iceberg orders
  - Stop orders

## Development

### Old Files (Backup)
The original monolithic files have been renamed:
- `main_old.py`
- `market_stream_old.py`
- `orderbook_viz_old.py`

These can be safely deleted once you confirm the new structure works.

### Running Individual Modules

```bash
# Test market stream
python -m simulation.market_stream

# Test visualization
python -m visualization.orderbook_viz
```

## License

MIT License - Feel free to use and modify!
