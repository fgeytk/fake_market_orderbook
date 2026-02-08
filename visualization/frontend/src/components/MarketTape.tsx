import { useEffect, useRef, useState } from 'react';
import { OrderbookSnapshot } from '../types/orderbook';

interface MarketTapeProps {
  snapshot: OrderbookSnapshot | null;
  maxRows?: number;
}

interface TapeRow {
  time: string;
  mid: number;
  spread: number;
  dir: 'up' | 'down' | 'flat';
}

export const MarketTape: React.FC<MarketTapeProps> = ({ snapshot, maxRows = 40 }) => {
  const [rows, setRows] = useState<TapeRow[]>([]);
  const lastMidRef = useRef<number | null>(null);

  useEffect(() => {
    if (!snapshot) return;

    const bestBid = snapshot.bids?.[0]?.[0];
    const bestAsk = snapshot.asks?.[0]?.[0];
    if (!bestBid || !bestAsk) return;

    const mid = (bestBid + bestAsk) / 2;
    const spread = Math.max(0, bestAsk - bestBid);
    const tsMs = Math.floor((snapshot.ts || Date.now() * 1e6) / 1e6);
    const time = new Date(tsMs).toLocaleTimeString();

    let dir: TapeRow['dir'] = 'flat';
    if (lastMidRef.current !== null) {
      if (mid > lastMidRef.current) dir = 'up';
      if (mid < lastMidRef.current) dir = 'down';
    }
    lastMidRef.current = mid;

    setRows((prev) => {
      const next = [{ time, mid, spread, dir }, ...prev];
      return next.slice(0, maxRows);
    });
  }, [snapshot, maxRows]);

  return (
    <div className="tape scroll-y">
      {rows.map((row, idx) => (
        <div key={`${row.time}-${idx}`} className={`tape-row ${row.dir}`}>
          <span>{row.time}</span>
          <span className="cell-right">{row.mid.toFixed(4)}</span>
          <span className="cell-right">{row.spread.toFixed(4)}</span>
        </div>
      ))}
    </div>
  );
};
