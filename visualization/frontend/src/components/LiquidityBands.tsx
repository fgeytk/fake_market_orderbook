import { OrderbookSnapshot } from '../types/orderbook';

interface LiquidityBandsProps {
  snapshot: OrderbookSnapshot | null;
}

export const LiquidityBands: React.FC<LiquidityBandsProps> = ({ snapshot }) => {
  if (!snapshot) return null;

  const bids = snapshot.bids ?? [];
  const asks = snapshot.asks ?? [];

  const topBid = sumLevels(bids.slice(0, 10));
  const topAsk = sumLevels(asks.slice(0, 10));
  const midBid = sumLevels(bids.slice(10, 30));
  const midAsk = sumLevels(asks.slice(10, 30));
  const tailBid = sumLevels(bids.slice(30));
  const tailAsk = sumLevels(asks.slice(30));

  const maxVal = Math.max(1, topBid, topAsk, midBid, midAsk, tailBid, tailAsk);

  const bands = [
    { label: 'Top 10 Bid', value: topBid },
    { label: 'Top 10 Ask', value: topAsk },
    { label: 'Mid 20 Bid', value: midBid },
    { label: 'Mid 20 Ask', value: midAsk },
    { label: 'Tail Bid', value: tailBid },
    { label: 'Tail Ask', value: tailAsk },
  ];

  return (
    <div className="bands">
      {bands.map((band) => (
        <div key={band.label} className="band-row">
          <span>{band.label}</span>
          <div className="band-bar">
            <div className="band-fill" style={{ width: `${(band.value / maxVal) * 100}%` }} />
          </div>
          <span className="cell-right">{band.value.toFixed(0)}</span>
        </div>
      ))}
    </div>
  );
};

function sumLevels(levels: [number, number][]): number {
  return levels.reduce((sum, [, size]) => sum + size, 0);
}
