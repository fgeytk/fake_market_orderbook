import { DepthChart } from './components/DepthChart';
import { Metrics } from './components/Metrics';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  const wsUrl = `ws://${window.location.hostname}:8000/ws`;
  const { snapshot, status, latency } = useWebSocket(wsUrl);

  return (
    <div style={styles.layout}>
      <div style={styles.main}>
        <div style={styles.panel}>
          <div style={styles.panelHeader}>
            <span>Depth Chart</span>
          </div>
          <div style={styles.chartContainer}>
            <DepthChart snapshot={snapshot} />
          </div>
        </div>
      </div>
      
      <aside style={styles.sidebar}>
        <Metrics snapshot={snapshot} latency={latency} status={status} />
      </aside>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  layout: {
    display: 'grid',
    gridTemplateColumns: 'minmax(0, 1fr) 340px',
    gap: '16px',
    padding: '16px',
    height: '100vh',
    background: '#0a0e17',
  },
  main: {
    display: 'flex',
    flexDirection: 'column',
    minHeight: 0,
  },
  panel: {
    background: '#141a26',
    border: '1px solid #1f2937',
    borderRadius: '14px',
    padding: '16px',
    display: 'flex',
    flexDirection: 'column',
    gap: '12px',
    height: '100%',
  },
  panelHeader: {
    fontSize: '12px',
    textTransform: 'uppercase',
    color: '#6b7280',
    letterSpacing: '0.05em',
    fontWeight: 600,
  },
  chartContainer: {
    flex: 1,
    minHeight: 0,
  },
  sidebar: {
    display: 'flex',
    flexDirection: 'column',
  },
};

export default App;
