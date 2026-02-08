import { useMemo, useRef } from 'react';
import { OrderbookSnapshot } from '../types/orderbook';

interface MarketSummaryProps {
  snapshot: OrderbookSnapshot | null;
}

export const MarketSummary: React.FC<MarketSummaryProps> = ({ snapshot }) => {
  const lastMidRef = useRef<number | null>(null);

  const summary = useMemo(() => {
    if (!snapshot) return null;

    const bestBid = snapshot.bids?.[0]?.[0] ?? 0;
    const bestAsk = snapshot.asks?.[0]?.[0] ?? 0;
    const mid = bestBid && bestAsk ? (bestBid + bestAsk) / 2 : 0;
    const spread = bestBid && bestAsk ? bestAsk - bestBid : 0;

    const bidVol = snapshot.bids.reduce((sum, [, size]) => sum + size, 0);
    const askVol = snapshot.asks.reduce((sum, [, size]) => sum + size, 0);
    const imbalance = bidVol + askVol > 0 ? (bidVol / (bidVol + askVol)) * 100 : 50;

    const topBid = sumLevels(snapshot.bids.slice(0, 10));
    const topAsk = sumLevels(snapshot.asks.slice(0, 10));

    let delta = 0;
    if (lastMidRef.current !== null) {
      delta = mid - lastMidRef.current;
    }
    lastMidRef.current = mid;

    return {
      mid,
      spread,
      imbalance,
      topBid,
      topAsk,
      bidVol,
      askVol,
      delta,
    };
  }, [snapshot]);

  if (!summary) {
    return <div className="summary-empty">Waiting for data...</div>;
  }

  return (
    <div className="summary-grid">
      <SummaryItem label="Mid" value={formatPrice(summary.mid)} />
      <SummaryItem label="Spread" value={summary.spread.toFixed(4)} />
      <SummaryItem label="Imbalance" value={`${summary.imbalance.toFixed(1)}%`} />
      <SummaryItem label="Top10 Bid" value={summary.topBid.toFixed(0)} />
      <SummaryItem label="Top10 Ask" value={summary.topAsk.toFixed(0)} />
      <SummaryItem
        label="Delta"
        value={summary.delta >= 0 ? `+${summary.delta.toFixed(4)}` : summary.delta.toFixed(4)}
        tone={summary.delta >= 0 ? 'up' : 'down'}
      />
      <SummaryItem label="Bid Vol" value={summary.bidVol.toFixed(0)} />
      <SummaryItem label="Ask Vol" value={summary.askVol.toFixed(0)} />
    </div>
  );
};

function sumLevels(levels: [number, number][]): number {
  return levels.reduce((sum, [, size]) => sum + size, 0);
}

function formatPrice(value: number): string {
  if (!value) return '0.0000';
  return value.toFixed(4);
}

const SummaryItem: React.FC<{ label: string; value: string; tone?: 'up' | 'down' }> = ({
  label,
  value,
  tone,
}) => (
  <div className={`summary-card ${tone ?? ''}`}>
    <div className="summary-label">{label}</div>
    <div className="summary-value">{value}</div>
  </div>
);
