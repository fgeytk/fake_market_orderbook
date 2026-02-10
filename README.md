# Orderbook Trading Simulation

A realistic limit orderbook with tick-based pricing, regime-driven market simulation, and live visualization.

**Highlights**
- Tick-based LOB with price-time priority and cancel-by-id support.
- ITCH-like L3 message objects (ADD, EXECUTE, CANCEL).
- Market simulation with regime switching and intraday activity/volatility curves.
- Agent-based flow (market maker, momentum, mean reversion, noise).
- WebSocket backend streaming MessagePack orderbook snapshots.
- Two UIs: legacy vanilla JS at `/ui`, modern React + Vite in `visualization/frontend`.
- Pytest + Hypothesis property tests.

**Project Structure**
```
IA/
|-- core/
|   |-- config.py
|   |-- models.py
|   |-- orderbook.py
|   `-- __init__.py
|-- simulation/
|   |-- config.py
|   |-- market_stream.py
|   |-- order_flow.py
|   |-- book_ops.py
|   |-- agents.py
|   |-- stochastic.py
|   `-- __init__.py
|-- visualization/
|   |-- ws_server.py
|   |-- web/                  # vanilla JS UI served at /ui
|   |-- frontend/             # React + Vite UI
|   `-- QUICKSTART.md
|-- tests/
|   |-- conftest.py
|   |-- test_orderbook.py
|   |-- test_models.py
|   |-- test_agents.py
|   |-- test_integration_market_stream.py
|   `-- test_invariants_property.py
|-- legacy/                   # old backups
|-- cli.py
|-- main.py
|-- requirements.txt
|-- start-backend.ps1
|-- start-frontend.ps1
|-- clean_caches.ps1
|-- watch_itch.py
|-- test_ws_itch.py
`-- README.md
```

**Setup**
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

**Quickstart**
- Backend (FastAPI + WebSocket):
```bash
python main.py ws --host 127.0.0.1 --port 8000
# or on Windows
.\start-backend.ps1
```
- Frontend (React dev server):
```bash
.\start-frontend.ps1
# or manually
cd visualization/frontend
npm install
npm run dev
```

Open `http://localhost:3000` for the React UI.
Open `http://localhost:8000/ui` for the legacy UI.

If you run `npm run build`, the React app is built into `visualization/frontend/dist` and will be served by FastAPI at `http://localhost:8000/` when that folder exists.

**CLI Usage**
```bash
# Stream a short run to stdout
python main.py stream --steps 20 --sleep-sec 0.0

# Profile the generator
python main.py profile --steps 2000

# Help
python main.py --help
```

**WebSocket Protocol**
- Endpoint: `ws://localhost:8000/ws`
- Payload fields: `ts`, `seq`, `bids`, `asks`
- `bids` and `asks` are lists of `[price, size]` (best first)

The WebSocket feed is snapshots, not L3 messages. If you need raw L3 events, use `simulation.stream_fake_market` directly.

Note: `watch_itch.py` and `test_ws_itch.py` expect JSON batches from an older feed and do not match the current MessagePack snapshot protocol.

**Library Usage**
```python
from core import Orderbook
from simulation import SimulationConfig, stream_fake_market

book = Orderbook()
cfg = SimulationConfig(seed=123, orders_per_tick=5, cancel_ratio=0.2)
gen = stream_fake_market(book, cfg)

msg = next(gen)  # L3Add | L3Execute | L3Cancel
print(msg)
```

You can also override config fields directly:
```python
gen = stream_fake_market(book, seed=123, orders_per_tick=5, cancel_ratio=0.2)
```

**Configuration**
- `core/config.py` contains `TICK_SIZE`, `DEBUG`, `VALIDATE_ORDERS`
- `simulation/config.py` (`SimulationConfig`) contains price/spread, order flow ratios, agent seeding, regime switching, multi-day session settings, and performance controls

**Tests**
```bash
python -m pytest -q
```

**License**
MIT
