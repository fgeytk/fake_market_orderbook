import { useEffect, useState } from 'react';
import { OrderbookSnapshot } from '../types/orderbook';

interface MetricsProps {
  snapshot: OrderbookSnapshot | null;
  latency: number;
  status: string;
}

export const Metrics: React.FC<MetricsProps> = ({ snapshot, latency, status }) => {
  const [fps, setFps] = useState(0);
  const [frameCount, setFrameCount] = useState(0);
  const [lastCheck, setLastCheck] = useState(Date.now());

  useEffect(() => {
    if (!snapshot) return;
    
    setFrameCount(prev => prev + 1);
    
    const now = Date.now();
    if (now - lastCheck >= 1000) {
      setFps(frameCount);
      setFrameCount(0);
      setLastCheck(now);
    }
  }, [snapshot, frameCount, lastCheck]);

  const spread = snapshot
    ? snapshot.asks[0]?.[0] - snapshot.bids[0]?.[0]
    : 0;

  const midPrice = snapshot && snapshot.bids[0] && snapshot.asks[0]
    ? (snapshot.bids[0][0] + snapshot.asks[0][0]) / 2
    : 0;

  const bidVol = snapshot?.bids.reduce((sum, [, size]) => sum + size, 0) || 0;
  const askVol = snapshot?.asks.reduce((sum, [, size]) => sum + size, 0) || 0;
  const imbalance = bidVol + askVol > 0 ? (bidVol / (bidVol + askVol)) * 100 : 50;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <div style={styles.brand}>
          <div style={styles.logo}>OB</div>
          <div>
            <div style={styles.title}>Orderbook Live</div>
            <div style={styles.subtitle}>HFT Edition</div>
          </div>
        </div>
        <div style={styles.stats}>
          <StatItem label="Latency" value={`${latency.toFixed(1)} ms`} />
          <StatItem label="FPS" value={`${fps}`} />
          <StatItem label="Seq" value={`${snapshot?.seq || '—'}`} />
          <StatItem
            label="Status"
            value={status}
            color={status === 'connected' ? '#10b981' : '#ef4444'}
          />
        </div>
      </div>
      
      <div style={styles.metrics}>
        <MetricCard label="Mid Price" value={`$${midPrice.toFixed(2)}`} />
        <MetricCard label="Spread" value={`$${spread.toFixed(3)}`} />
        <MetricCard
          label="Imbalance"
          value={`${imbalance.toFixed(1)}%`}
          subtitle={`${bidVol} / ${askVol}`}
        />
      </div>

      <div style={styles.book}>
        <BookRow
          label="Best Bid"
          price={snapshot?.bids[0]?.[0]}
          size={snapshot?.bids[0]?.[1]}
          color="#10b981"
        />
        <BookRow
          label="Best Ask"
          price={snapshot?.asks[0]?.[0]}
          size={snapshot?.asks[0]?.[1]}
          color="#ef4444"
        />
      </div>
    </div>
  );
};

const StatItem: React.FC<{ label: string; value: string; color?: string }> = ({
  label,
  value,
  color,
}) => (
  <div style={styles.stat}>
    <div style={styles.statLabel}>{label}</div>
    <div style={{ ...styles.statValue, color }}>{value}</div>
  </div>
);

const MetricCard: React.FC<{ label: string; value: string; subtitle?: string }> = ({
  label,
  value,
  subtitle,
}) => (
  <div style={styles.card}>
    <div style={styles.cardLabel}>{label}</div>
    <div style={styles.cardValue}>{value}</div>
    {subtitle && <div style={styles.cardSubtitle}>{subtitle}</div>}
  </div>
);

const BookRow: React.FC<{
  label: string;
  price?: number;
  size?: number;
  color: string;
}> = ({ label, price, size, color }) => (
  <div style={styles.row}>
    <span style={{ ...styles.rowLabel, color }}>{label}</span>
    <span style={styles.rowValue}>
      {price && size
        ? `$${price.toFixed(2)} × ${size} = $${(price * size).toFixed(2)}`
        : '—'}
    </span>
  </div>
);

const styles: Record<string, React.CSSProperties> = {
  container: {
    display: 'flex',
    flexDirection: 'column',
    gap: '16px',
    height: '100%',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '16px',
    background: '#0d1117',
    borderRadius: '12px',
    border: '1px solid #1f2937',
  },
  brand: {
    display: 'flex',
    gap: '12px',
    alignItems: 'center',
  },
  logo: {
    width: '40px',
    height: '40px',
    borderRadius: '10px',
    background: 'linear-gradient(135deg, #3b82f6, #8b5cf6)',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    fontWeight: 700,
    fontSize: '14px',
  },
  title: {
    fontSize: '15px',
    fontWeight: 600,
  },
  subtitle: {
    fontSize: '11px',
    color: '#6b7280',
  },
  stats: {
    display: 'flex',
    gap: '16px',
  },
  stat: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'flex-end',
  },
  statLabel: {
    fontSize: '9px',
    color: '#6b7280',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
  },
  statValue: {
    fontSize: '13px',
    fontWeight: 600,
    fontFamily: 'monospace',
  },
  metrics: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
    gap: '12px',
  },
  card: {
    background: '#0d1117',
    padding: '12px',
    borderRadius: '10px',
    border: '1px solid #1f2937',
  },
  cardLabel: {
    fontSize: '10px',
    color: '#6b7280',
    textTransform: 'uppercase',
    marginBottom: '4px',
  },
  cardValue: {
    fontSize: '18px',
    fontWeight: 700,
    fontFamily: 'monospace',
  },
  cardSubtitle: {
    fontSize: '10px',
    color: '#6b7280',
    marginTop: '2px',
  },
  book: {
    display: 'flex',
    flexDirection: 'column',
    gap: '8px',
    flex: 1,
  },
  row: {
    display: 'flex',
    justifyContent: 'space-between',
    padding: '12px',
    background: '#0d1117',
    borderRadius: '10px',
    border: '1px solid #1f2937',
  },
  rowLabel: {
    fontSize: '11px',
    fontWeight: 600,
    textTransform: 'uppercase',
  },
  rowValue: {
    fontSize: '12px',
    fontFamily: 'monospace',
    fontWeight: 600,
  },
};
