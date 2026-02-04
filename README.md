# Orderbook Trading Simulation

A realistic limit orderbook implementation with tick-based pricing, regime-based market simulation, and interactive visualization.

## Project Structure

```
IA/
├── core/                      # Core orderbook engine
│   ├── __init__.py
│   ├── config.py             # Configuration constants (TICK_SIZE, DEBUG)
│   ├── logging_config.py     # Logging configuration
│   ├── models.py             # Data models (Order, Trade, CancelEvent, Side, OrderType)
│   └── orderbook.py          # Orderbook class with matching engine
│
├── simulation/               # Market simulation
│   ├── __init__.py
│   ├── agents.py             # Agent behaviors
│   └── market_stream.py      # Realistic market data generator
│   └── stochastic.py         # Mid-price evolution
│
├── visualization/            # Interactive UI
│   ├── __init__.py
│   ├── ws_server.py          # FastAPI + WebSocket backend
│   └── web/                  # HTML/CSS/JS front-end
│
├── tests/                     # Pytest suite
│   ├── conftest.py
│   ├── test_agents.py
│   ├── test_integration_market_stream.py
│   ├── test_invariants_property.py
│   ├── test_models.py
│   └── test_orderbook.py
│
├── cli.py                     # Typer CLI commands (viz/stream/profile)
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

### Run Web UI (FastAPI + WebSocket)

```bash
python main.py ws --host 127.0.0.1 --port 8000
```

Then open http://127.0.0.1:8000/ui in your browser.

### Run a Short Stream

```bash
python main.py stream --steps 20
```

### CLI Help

```bash
python main.py --help
```

### Tests (pytest)

```bash
# Run all tests
python -m pytest -q

# Run a single test file
python -m pytest tests/test_orderbook.py -q
```

Notes:
- Les tests unitaires sont dans tests/.
- Hypothesis est utilisé pour les tests d'invariants (test_invariants_property.py).

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
- `VALIDATE_ORDERS`: Validate orders on creation (default: False)

Other runtime parameters are CLI options:
- `main.py ws --host --port`
- `main.py stream --steps --sleep-sec`
- `main.py profile --steps --sleep-sec`

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
cli.py stream (prints)
FastAPI WS + web UI (visualization)
```

### Simple(dumb) Orderbook

### Old Files (Backup)
Legacy files are kept in legacy/:
- `main_old.py`
- `market_stream_old.py`
- `orderbook_viz_old.py`
- `orderbook_viz_dash.py`

These can be safely deleted once you confirm the new structure works.

### Running Individual Modules

```bash
# Test market stream
python -m simulation.market_stream
```

## License

MIT License - Feel free to use and modify!
