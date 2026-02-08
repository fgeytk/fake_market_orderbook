import { useState } from 'react';
import { DepthChart } from './components/DepthChart';
import { Metrics } from './components/Metrics';
import { PriceChart } from './components/PriceChart';
import { OrderbookTable } from './components/OrderbookTable';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  const wsUrl = `ws://${window.location.hostname}:8000/ws`;
  const { snapshot, status, latency } = useWebSocket(wsUrl);
  const [zoom, setZoom] = useState(1);

  return (
    <div style={styles.layout}>
      <header style={styles.topbar}>
        <div style={styles.brand}>
          <div style={styles.logo}>OB</div>
          <div>
            <div style={styles.title}>Orderbook Studio</div>
            <div style={styles.subtitle}>Depth + Price view</div>
          </div>
        </div>
        <div style={styles.controls}>
          <span style={styles.controlLabel}>Depth zoom</span>
          <input
            type="range"
            min={1}
            max={6}
            step={0.5}
            value={zoom}
            onChange={(e) => setZoom(Number(e.target.value))}
            style={styles.zoomRange}
          />
          <button style={styles.zoomButton} onClick={() => setZoom(1)}>
            Reset
          </button>
          <div style={styles.status}>
            <span style={styles.statusDot(status)} />
            <span>{status}</span>
          </div>
        </div>
      </header>

      <div style={styles.body}>
        <div style={styles.leftColumn}>
          <div style={styles.panel}>
            <div style={styles.panelHeader}>Price (mid)</div>
            <div style={styles.chartContainer}>
              <PriceChart snapshot={snapshot} />
            </div>
          </div>

          <div style={styles.panel}>
            <div style={styles.panelHeader}>Depth chart</div>
            <div style={styles.chartContainer}>
              <DepthChart snapshot={snapshot} zoom={zoom} />
            </div>
          </div>
        </div>

        <aside style={styles.rightColumn}>
          <div style={styles.panel}>
            <OrderbookTable snapshot={snapshot} levels={60} />
          </div>
          <div style={styles.panelCompact}>
            <Metrics snapshot={snapshot} latency={latency} status={status} />
          </div>
        </aside>
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  layout: {
    display: 'flex',
    flexDirection: 'column',
    height: '100vh',
    background: 'radial-gradient(circle at top, #0d1221, #070b12 60%)',
  },
  topbar: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: '16px 20px',
    borderBottom: '1px solid #1f2937',
    background: 'rgba(12, 16, 28, 0.9)',
    backdropFilter: 'blur(8px)',
  },
  brand: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
  },
  logo: {
    width: '40px',
    height: '40px',
    borderRadius: '10px',
    display: 'grid',
    placeItems: 'center',
    background: 'linear-gradient(135deg, #1d4ed8, #38bdf8)',
    fontWeight: 700,
  },
  title: {
    fontSize: '16px',
    fontWeight: 700,
    color: '#e2e8f0',
  },
  subtitle: {
    fontSize: '12px',
    color: '#94a3b8',
  },
  controls: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    color: '#94a3b8',
    fontSize: '12px',
  },
  controlLabel: {
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    fontSize: '10px',
  },
  zoomRange: {
    width: '140px',
  },
  zoomButton: {
    background: '#0d1117',
    border: '1px solid #1f2937',
    borderRadius: '8px',
    color: '#e5e7eb',
    fontSize: '10px',
    padding: '4px 8px',
    cursor: 'pointer',
  },
  status: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
  },
  statusDot: (status: string) => ({
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    background: status === 'connected' ? '#22c55e' : '#f97316',
  }),
  body: {
    display: 'grid',
    gridTemplateColumns: 'minmax(0, 1fr) 420px',
    gap: '16px',
    padding: '16px',
    flex: 1,
    minHeight: 0,
  },
  leftColumn: {
    display: 'grid',
    gridTemplateRows: 'minmax(200px, 1fr) minmax(240px, 1.2fr)',
    gap: '16px',
    minHeight: 0,
  },
  rightColumn: {
    display: 'grid',
    gridTemplateRows: 'minmax(0, 1fr) auto',
    gap: '16px',
    minHeight: 0,
  },
  panel: {
    background: 'rgba(15, 23, 42, 0.85)',
    border: '1px solid #1f2937',
    borderRadius: '16px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    minHeight: 0,
  },
  panelCompact: {
    background: 'rgba(15, 23, 42, 0.85)',
    border: '1px solid #1f2937',
    borderRadius: '16px',
    padding: '12px',
  },
  panelHeader: {
    fontSize: '12px',
    textTransform: 'uppercase',
    color: '#94a3b8',
    letterSpacing: '0.08em',
    fontWeight: 600,
  },
  chartContainer: {
    flex: 1,
    minHeight: 0,
  },
};

export default App;
