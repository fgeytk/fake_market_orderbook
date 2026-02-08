import { DepthChart } from './components/DepthChart';
import { PriceChart } from './components/PriceChart';
import { OrderbookTable } from './components/OrderbookTable';
import { LiquidityBands } from './components/LiquidityBands';
import { FlowMetrics } from './components/FlowMetrics';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  const wsUrl = `ws://${window.location.hostname}:8000/ws`;
  const { snapshot, status, latency } = useWebSocket(wsUrl);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-badge">OB</div>
          <div>
            <div className="brand-title">Orderbook Studio Pro</div>
            <div className="brand-subtitle">Depth, price, and flow</div>
          </div>
        </div>
        <div className="topbar-right">
          <span>Latency {latency.toFixed(1)} ms</span>
          <span>Seq {snapshot?.seq ?? '—'}</span>
          <div className="status-pill">
            <span className={`status-dot ${status === 'connected' ? 'connected' : ''}`} />
            <span>{status}</span>
          </div>
        </div>
      </header>

      <main className="layout">
        <section className="left-stack">
          <div className="panel">
            <div className="panel-title">Price</div>
            <div className="panel-body">
              <PriceChart snapshot={snapshot} />
            </div>
          </div>
          <div className="panel">
            <div className="panel-title">Depth</div>
            <div className="panel-body">
              <DepthChart snapshot={snapshot} />
            </div>
          </div>
        </section>

        <aside className="right-stack">
          <div className="panel">
            <OrderbookTable snapshot={snapshot} levels={80} />
          </div>
          <div className="panel">
            <div className="panel-title">Liquidity bands</div>
            <LiquidityBands snapshot={snapshot} />
          </div>
          <div className="panel">
            <div className="panel-title">Flow metrics</div>
            <FlowMetrics snapshot={snapshot} />
          </div>
        </aside>
      </main>
    </div>
  );
}

export default App;
