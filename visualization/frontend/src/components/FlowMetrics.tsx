import { useEffect, useRef, useState } from 'react';
import { OrderbookSnapshot } from '../types/orderbook';

interface FlowMetricsProps {
  snapshot: OrderbookSnapshot | null;
}

interface MidPoint {
  ts: number;
  mid: number;
}

export const FlowMetrics: React.FC<FlowMetricsProps> = ({ snapshot }) => {
  const seriesRef = useRef<MidPoint[]>([]);
  const [stats, setStats] = useState(() => ({
    mid: 0,
    spread: 0,
    imbalance: 50,
    topBid: 0,
    topAsk: 0,
    tailBid: 0,
    tailAsk: 0,
    vol: 0,
    delta: 0,
  }));

  useEffect(() => {
    if (!snapshot) return;

    const bestBid = snapshot.bids?.[0]?.[0] ?? 0;
    const bestAsk = snapshot.asks?.[0]?.[0] ?? 0;
    if (!bestBid || !bestAsk) return;

    const mid = (bestBid + bestAsk) / 2;
    const spread = Math.max(0, bestAsk - bestBid);
    const bidVol = sumLevels(snapshot.bids);
    const askVol = sumLevels(snapshot.asks);
    const imbalance = bidVol + askVol > 0 ? (bidVol / (bidVol + askVol)) * 100 : 50;
    const topBid = sumLevels(snapshot.bids.slice(0, 10));
    const topAsk = sumLevels(snapshot.asks.slice(0, 10));
    const tailBid = sumLevels(snapshot.bids.slice(30));
    const tailAsk = sumLevels(snapshot.asks.slice(30));

    const ts = snapshot.ts || Date.now() * 1e6;
    const series = seriesRef.current;
    series.push({ ts, mid });
    if (series.length > 240) {
      series.splice(0, series.length - 240);
    }

    const values = series.map((p) => p.mid);
    const mean = values.reduce((sum, v) => sum + v, 0) / values.length;
    const variance = values.reduce((sum, v) => sum + (v - mean) ** 2, 0) / values.length;
    const vol = Math.sqrt(variance);

    const prev = series.length > 1 ? series[series.length - 2].mid : mid;
    const delta = mid - prev;

    setStats({
      mid,
      spread,
      imbalance,
      topBid,
      topAsk,
      tailBid,
      tailAsk,
      vol,
      delta,
    });
  }, [snapshot]);

  return (
    <div className="stats-scroll">
      <div className="stats-grid">
        <StatCard label="Mid" value={stats.mid.toFixed(4)} />
        <StatCard label="Spread" value={stats.spread.toFixed(4)} />
        <StatCard label="Imbalance" value={`${stats.imbalance.toFixed(1)}%`} />
        <StatCard label="Vol" value={stats.vol.toFixed(5)} />
        <StatCard label="Top10 Bid" value={stats.topBid.toFixed(0)} />
        <StatCard label="Top10 Ask" value={stats.topAsk.toFixed(0)} />
        <StatCard label="Tail Bid" value={stats.tailBid.toFixed(0)} />
        <StatCard label="Tail Ask" value={stats.tailAsk.toFixed(0)} />
        <StatCard
          label="Delta"
          value={stats.delta >= 0 ? `+${stats.delta.toFixed(4)}` : stats.delta.toFixed(4)}
          tone={stats.delta >= 0 ? 'up' : 'down'}
        />
      </div>
      <div className="stats-section">Options coming soon</div>
      <div className="stats-grid">
        <StatCard label="Delta" value="—" />
        <StatCard label="Gamma" value="—" />
        <StatCard label="Vega" value="—" />
        <StatCard label="Theta" value="—" />
        <StatCard label="Rho" value="—" />
        <StatCard label="Charm" value="—" />
        <StatCard label="Vanna" value="—" />
        <StatCard label="Vomma" value="—" />
      </div>
    </div>
  );
};

function sumLevels(levels: [number, number][]): number {
  return levels.reduce((sum, [, size]) => sum + size, 0);
}

const StatCard: React.FC<{ label: string; value: string; tone?: 'up' | 'down' }> = ({
  label,
  value,
  tone,
}) => (
  <div className={`stats-card ${tone ?? ''}`}>
    <div className="stats-label">{label}</div>
    <div className="stats-value">{value}</div>
  </div>
);
