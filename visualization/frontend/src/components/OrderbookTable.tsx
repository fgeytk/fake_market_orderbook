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
    <div style={styles.container}>
      <div style={styles.header}>Orderbook Depth</div>
      <div style={styles.columns}>
        <div style={styles.column}>
          <div style={styles.columnHeader}>Bids</div>
          <div style={styles.rows}>
            {bidRows.map((row, idx) => (
              <div key={`bid-${idx}`} style={styles.row}>
                <div style={styles.barBid(maxSize, row.size)} />
                <span style={styles.priceBid}>{row.price.toFixed(4)}</span>
                <span style={styles.size}>{row.size}</span>
                <span style={styles.cum}>{row.cum}</span>
              </div>
            ))}
          </div>
        </div>
        <div style={styles.column}>
          <div style={styles.columnHeader}>Asks</div>
          <div style={styles.rows}>
            {askRows.map((row, idx) => (
              <div key={`ask-${idx}`} style={styles.row}>
                <div style={styles.barAsk(maxSize, row.size)} />
                <span style={styles.priceAsk}>{row.price.toFixed(4)}</span>
                <span style={styles.size}>{row.size}</span>
                <span style={styles.cum}>{row.cum}</span>
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

const styles = {
  container: {
    background: '#0f172a',
    border: '1px solid #1f2937',
    borderRadius: '12px',
    padding: '12px',
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '10px',
    height: '100%',
  },
  header: {
    fontSize: '12px',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.08em',
    color: '#94a3b8',
    fontWeight: 600,
  },
  columns: {
    display: 'grid',
    gridTemplateColumns: '1fr 1fr',
    gap: '12px',
    flex: 1,
    minHeight: 0,
  },
  column: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '6px',
    minHeight: 0,
  },
  columnHeader: {
    fontSize: '11px',
    color: '#64748b',
    textTransform: 'uppercase' as const,
    letterSpacing: '0.06em',
  },
  rows: {
    display: 'flex',
    flexDirection: 'column' as const,
    gap: '4px',
    overflow: 'auto' as const,
    paddingRight: '4px',
  },
  row: {
    position: 'relative' as const,
    display: 'grid',
    gridTemplateColumns: '1fr 1fr 1fr',
    gap: '6px',
    alignItems: 'center',
    padding: '6px 8px',
    borderRadius: '8px',
    background: '#0b111c',
    border: '1px solid #1f2937',
    fontFamily: 'monospace',
    fontSize: '11px',
    color: '#e2e8f0',
  },
  priceBid: {
    color: '#22c55e',
    zIndex: 2,
  },
  priceAsk: {
    color: '#ef4444',
    zIndex: 2,
  },
  size: {
    textAlign: 'right' as const,
    zIndex: 2,
  },
  cum: {
    textAlign: 'right' as const,
    color: '#94a3b8',
    zIndex: 2,
  },
  barBid: (max: number, size: number) => ({
    position: 'absolute' as const,
    left: 0,
    top: 0,
    bottom: 0,
    width: `${Math.min(100, (size / max) * 100)}%`,
    background: 'rgba(34, 197, 94, 0.12)',
    borderRadius: '8px',
    zIndex: 1,
  }),
  barAsk: (max: number, size: number) => ({
    position: 'absolute' as const,
    left: 0,
    top: 0,
    bottom: 0,
    width: `${Math.min(100, (size / max) * 100)}%`,
    background: 'rgba(239, 68, 68, 0.12)',
    borderRadius: '8px',
    zIndex: 1,
  }),
};
