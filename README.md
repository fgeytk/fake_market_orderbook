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

### Core Orderbook Dummy
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

### Simple(dumb) Orderbook

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
