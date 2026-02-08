import { useEffect, useRef } from 'react';
import { OrderbookSnapshot } from '../types/orderbook';

interface DepthChartProps {
  snapshot: OrderbookSnapshot | null;
  zoom: number;
}

export const DepthChart: React.FC<DepthChartProps> = ({ snapshot, zoom }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) {
      console.error('Canvas 2D not supported');
      return;
    }

    ctxRef.current = ctx;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };

    resize();
    window.addEventListener('resize', resize);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  useEffect(() => {
    if (!ctxRef.current) return;

    const ctx = ctxRef.current;
    const canvas = canvasRef.current!;

    const render = () => {
      // Background
      const width = canvas.width / (window.devicePixelRatio || 1);
      const height = canvas.height / (window.devicePixelRatio || 1);
      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#0a0f19';
      ctx.fillRect(0, 0, width, height);

      if (!snapshot) {
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px monospace';
        ctx.fillText('Waiting for data...', 16, 24);
        return;
      }

      const { bids, asks } = snapshot;
      const midX = width / 2;

      const maxLevels = Math.max(bids.length, asks.length);
      const rows = Math.max(10, Math.floor((height - 40) / Math.max(1, zoom)));
      const barHeight = Math.max(1, (height - 40) / (Math.min(maxLevels, rows) + 2));

      const binnedBids = compressLevels(bids, rows);
      const binnedAsks = compressLevels(asks, rows);

      const maxSize = Math.max(
        1,
        ...binnedBids.map(b => b[1]),
        ...binnedAsks.map(a => a[1])
      );

      const scale = (width * 0.42) / maxSize;

      // Headers
      ctx.font = '11px monospace';
      ctx.fillStyle = '#6b7280';
      ctx.fillText('BID', midX - 35, 18);
      ctx.fillText('ASK', midX + 10, 18);

      // Bids
      binnedBids.forEach(([price, size], idx) => {
        const barWidth = size * scale;
        const y = 30 + idx * barHeight;

        ctx.fillStyle = 'rgba(16, 185, 129, 0.85)';
        ctx.fillRect(midX - barWidth, y, barWidth - 1, barHeight - 1);

        ctx.fillStyle = '#e5e7eb';
        ctx.font = '10px monospace';
        ctx.textAlign = 'right';
        ctx.fillText(`${price.toFixed(2)}`, midX - barWidth - 8, y + barHeight * 0.65);
        ctx.fillText(`${size}`, midX - 4, y + barHeight * 0.65);
      });

      // Asks
      binnedAsks.forEach(([price, size], idx) => {
        const barWidth = size * scale;
        const y = 30 + idx * barHeight;

        ctx.fillStyle = 'rgba(239, 68, 68, 0.85)';
        ctx.fillRect(midX + 1, y, barWidth, barHeight - 1);

        ctx.fillStyle = '#e5e7eb';
        ctx.font = '10px monospace';
        ctx.textAlign = 'left';
        ctx.fillText(`${price.toFixed(2)}`, midX + barWidth + 8, y + barHeight * 0.65);
        ctx.fillText(`${size}`, midX + 4, y + barHeight * 0.65);
      });

    };

    rafRef.current = requestAnimationFrame(render);
  }, [snapshot, zoom]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        width: '100%',
        height: '100%',
        borderRadius: '12px',
        border: '1px solid #1f2937',
      }}
    />
  );
};

function compressLevels(levels: [number, number][], rows: number): [number, number][] {
  if (levels.length <= rows) return levels;

  const binSize = Math.ceil(levels.length / rows);
  const result: [number, number][] = [];
  for (let i = 0; i < levels.length; i += binSize) {
    const slice = levels.slice(i, i + binSize);
    const size = slice.reduce((sum, [, qty]) => sum + qty, 0);
    const price = slice[slice.length - 1][0];
    result.push([price, size]);
  }

  return result;
}
