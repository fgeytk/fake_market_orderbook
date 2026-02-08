import { useEffect, useRef, useCallback, useState } from 'react';
import { OrderbookSnapshot } from '../types/orderbook';

interface UseWebSocketReturn {
  snapshot: OrderbookSnapshot | null;
  status: 'connecting' | 'connected' | 'disconnected';
  latency: number;
}

export const useWebSocket = (url: string): UseWebSocketReturn => {
  const [snapshot, setSnapshot] = useState<OrderbookSnapshot | null>(null);
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('connecting');
  const [latency, setLatency] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const workerRef = useRef<Worker | null>(null);

  const connect = useCallback(() => {
    if (!workerRef.current) {
      workerRef.current = new Worker(
        new URL('../workers/msgpack.worker.ts', import.meta.url),
        { type: 'module' }
      );
      
      workerRef.current.onmessage = (e) => {
        const { result } = e.data;
        if (result) {
          const now = Date.now() * 1e6;
          const latencyNs = Math.max(0, now - result.ts);
          setLatency(latencyNs / 1e6);
          setSnapshot(result);
        }
      };
    }

    const ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => setStatus('connected');
    
    ws.onclose = () => {
      setStatus('disconnected');
      setTimeout(connect, 1000);
    };

    ws.onmessage = (event) => {
      if (event.data && workerRef.current) {
        workerRef.current.postMessage({
          data: new Uint8Array(event.data),
          id: Date.now(),
        });
      }
    };
  }, [url]);

  useEffect(() => {
    connect();
    
    return () => {
      wsRef.current?.close();
      workerRef.current?.terminate();
    };
  }, [connect]);

  return { snapshot, status, latency };
};
