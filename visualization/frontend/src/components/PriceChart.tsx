import { useEffect, useRef } from 'react';
import { OrderbookSnapshot } from '../types/orderbook';

interface PriceChartProps {
  snapshot: OrderbookSnapshot | null;
}

interface PricePoint {
  ts: number;
  price: number;
}

export const PriceChart: React.FC<PriceChartProps> = ({ snapshot }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const ctxRef = useRef<CanvasRenderingContext2D | null>(null);
  const seriesRef = useRef<PricePoint[]>([]);
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
    if (!snapshot || !ctxRef.current) return;

    const bestBid = snapshot.bids?.[0]?.[0];
    const bestAsk = snapshot.asks?.[0]?.[0];
    if (!bestBid || !bestAsk) return;

    const mid = (bestBid + bestAsk) / 2;
    const ts = snapshot.ts || Date.now() * 1e6;

    const series = seriesRef.current;
    series.push({ ts, price: mid });
    if (series.length > 1200) {
      series.splice(0, series.length - 1200);
    }

    const ctx = ctxRef.current;
    const canvas = canvasRef.current!;

    const render = () => {
      const width = canvas.width / (window.devicePixelRatio || 1);
      const height = canvas.height / (window.devicePixelRatio || 1);

      ctx.clearRect(0, 0, width, height);
      ctx.fillStyle = '#0b111c';
      ctx.fillRect(0, 0, width, height);

      if (series.length < 2) {
        ctx.fillStyle = '#6b7280';
        ctx.font = '12px monospace';
        ctx.fillText('Collecting price...', 16, 24);
        return;
      }

      const prices = series.map((p) => p.price);
      const min = Math.min(...prices);
      const max = Math.max(...prices);
      const range = Math.max(1e-9, max - min);

      const padding = { top: 16, right: 20, bottom: 22, left: 52 };
      const plotWidth = width - padding.left - padding.right;
      const plotHeight = height - padding.top - padding.bottom;

      // Grid
      ctx.strokeStyle = '#1f2937';
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (let i = 0; i <= 4; i += 1) {
        const y = padding.top + (plotHeight * i) / 4;
        ctx.moveTo(padding.left, y);
        ctx.lineTo(width - padding.right, y);
      }
      ctx.stroke();

      // Price line
      ctx.strokeStyle = '#60a5fa';
      ctx.lineWidth = 2;
      ctx.beginPath();
      series.forEach((point, idx) => {
        const x = padding.left + (plotWidth * idx) / (series.length - 1);
        const y = padding.top + plotHeight * (1 - (point.price - min) / range);
        if (idx === 0) {
          ctx.moveTo(x, y);
        } else {
          ctx.lineTo(x, y);
        }
      });
      ctx.stroke();

      // Last price label
      const last = series[series.length - 1];
      ctx.fillStyle = '#e5e7eb';
      ctx.font = '12px monospace';
      ctx.fillText(`Mid: ${last.price.toFixed(4)}`, padding.left, height - 6);

      // Axis labels
      ctx.fillStyle = '#9ca3af';
      ctx.font = '11px monospace';
      ctx.fillText(max.toFixed(4), 8, padding.top + 10);
      ctx.fillText(min.toFixed(4), 8, padding.top + plotHeight);
    };

    rafRef.current = requestAnimationFrame(render);
  }, [snapshot]);

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
