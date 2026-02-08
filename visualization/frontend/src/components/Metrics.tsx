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
    <div className="metrics-grid">
      <MetricCard label="Latency" value={`${latency.toFixed(1)} ms`} />
      <MetricCard label="FPS" value={`${fps}`} />
      <MetricCard label="Seq" value={`${snapshot?.seq || '—'}`} />
      <MetricCard label="Status" value={status} />
      <MetricCard label="Mid Price" value={`$${midPrice.toFixed(2)}`} />
      <MetricCard label="Spread" value={`$${spread.toFixed(3)}`} />
      <MetricCard
        label="Imbalance"
        value={`${imbalance.toFixed(1)}%`}
        subtitle={`${bidVol} / ${askVol}`}
      />
      <MetricCard
        label="Best Bid"
        value={snapshot?.bids[0]?.[0] ? `$${snapshot.bids[0][0].toFixed(2)}` : '—'}
        subtitle={snapshot?.bids[0]?.[1] ? `${snapshot.bids[0][1]} size` : ''}
      />
      <MetricCard
        label="Best Ask"
        value={snapshot?.asks[0]?.[0] ? `$${snapshot.asks[0][0].toFixed(2)}` : '—'}
        subtitle={snapshot?.asks[0]?.[1] ? `${snapshot.asks[0][1]} size` : ''}
      />
    </div>
  );
};

const MetricCard: React.FC<{ label: string; value: string; subtitle?: string }> = ({
  label,
  value,
  subtitle,
}) => (
  <div className="metric-card">
    <div className="metric-label">{label}</div>
    <div className="metric-value">{value}</div>
    {subtitle ? <div className="metric-sub">{subtitle}</div> : null}
  </div>
);
