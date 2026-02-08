import { useEffect, useRef } from 'react';
import { OrderbookSnapshot } from '../types/orderbook';

interface DepthChartProps {
  snapshot: OrderbookSnapshot | null;
}

export const DepthChart: React.FC<DepthChartProps> = ({ snapshot }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const glRef = useRef<WebGLRenderingContext | null>(null);
  const rafRef = useRef<number>(0);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const gl = canvas.getContext('webgl', {
      alpha: false,
      antialias: false,
      depth: false,
    });

    if (!gl) {
      console.error('WebGL not supported, falling back to 2D');
      return;
    }

    glRef.current = gl;

    const resize = () => {
      const dpr = window.devicePixelRatio || 1;
      const rect = canvas.getBoundingClientRect();
      canvas.width = rect.width * dpr;
      canvas.height = rect.height * dpr;
      gl.viewport(0, 0, canvas.width, canvas.height);
    };

    resize();
    window.addEventListener('resize', resize);

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(rafRef.current);
    };
  }, []);

  useEffect(() => {
    if (!snapshot || !glRef.current) return;

    const gl = glRef.current;
    const canvas = canvasRef.current!;

    const render = () => {
      // Clear
      gl.clearColor(0.04, 0.06, 0.09, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT);

      // Simple 2D rendering for MVP (WebGL shaders would go here for production)
      const ctx = canvas.getContext('2d');
      if (!ctx) return;

      const { bids, asks } = snapshot;
      const width = canvas.width / (window.devicePixelRatio || 1);
      const height = canvas.height / (window.devicePixelRatio || 1);
      const midX = width / 2;

      ctx.save();
      ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);

      // Background
      ctx.fillStyle = '#0a0f19';
      ctx.fillRect(0, 0, width, height);

      const maxLevels = Math.max(bids.length, asks.length);
      const barHeight = Math.max(4, (height - 40) / (maxLevels + 2));

      const maxSize = Math.max(
        1,
        ...bids.map(b => b[1]),
        ...asks.map(a => a[1])
      );

      const scale = (width * 0.42) / maxSize;

      // Headers
      ctx.font = '11px monospace';
      ctx.fillStyle = '#6b7280';
      ctx.fillText('BID', midX - 35, 18);
      ctx.fillText('ASK', midX + 10, 18);

      // Bids
      bids.forEach(([price, size], idx) => {
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
      asks.forEach(([price, size], idx) => {
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

      ctx.restore();
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
