import { OrderbookSnapshot } from '../types/orderbook';

interface OrderbookTableProps {
  snapshot: OrderbookSnapshot | null;
  levels?: number;
}

interface RowData {
  price: number;
  size: number;
  cum: number;
}

export const OrderbookTable: React.FC<OrderbookTableProps> = ({ snapshot, levels = 40 }) => {
  const bids = snapshot?.bids ?? [];
  const asks = snapshot?.asks ?? [];

  const bidRows = buildRows(bids.slice(0, levels));
  const askRows = buildRows(asks.slice(0, levels));

  const maxSize = Math.max(
    1,
    ...bidRows.map((row) => row.size),
    ...askRows.map((row) => row.size)
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', height: '100%' }}>
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', flex: 1, minHeight: 0 }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', minHeight: 0 }}>
          <div className="book-header">
            <span>Price</span>
            <span className="cell-right">Size</span>
            <span className="cell-right">Cum</span>
          </div>
          <div className="scroll-y" style={{ display: 'flex', flexDirection: 'column', gap: '4px', paddingRight: '4px' }}>
            {bidRows.map((row, idx) => (
              <div key={`bid-${idx}`} className="book-row">
                <div className="bar bid" style={{ width: `${Math.min(100, (row.size / maxSize) * 100)}%` }} />
                <span className="price-bid">{row.price.toFixed(4)}</span>
                <span className="cell-right">{row.size}</span>
                <span className="cell-right">{row.cum}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', minHeight: 0 }}>
          <div className="book-header">
            <span>Price</span>
            <span className="cell-right">Size</span>
            <span className="cell-right">Cum</span>
          </div>
          <div className="scroll-y" style={{ display: 'flex', flexDirection: 'column', gap: '4px', paddingRight: '4px' }}>
            {askRows.map((row, idx) => (
              <div key={`ask-${idx}`} className="book-row">
                <div className="bar ask" style={{ width: `${Math.min(100, (row.size / maxSize) * 100)}%` }} />
                <span className="price-ask">{row.price.toFixed(4)}</span>
                <span className="cell-right">{row.size}</span>
                <span className="cell-right">{row.cum}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

function buildRows(levels: [number, number][]): RowData[] {
  let cum = 0;
  return levels.map(([price, size]) => {
    cum += size;
    return { price, size, cum };
  });
}

