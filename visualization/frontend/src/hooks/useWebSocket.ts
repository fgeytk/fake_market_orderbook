import { useEffect, useRef, useCallback, useState } from 'react';
import { decode } from '@msgpack/msgpack';
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
  const textDecoderRef = useRef<TextDecoder | null>(null);

  const connect = useCallback(() => {
    if (!textDecoderRef.current) {
      textDecoderRef.current = new TextDecoder();
    }

    const ws = new WebSocket(url);
    ws.binaryType = 'arraybuffer';
    wsRef.current = ws;

    ws.onopen = () => setStatus('connected');
    
    ws.onclose = () => {
      setStatus('disconnected');
      setTimeout(connect, 1000);
    };

    ws.onmessage = async (event) => {
      if (!event.data) return;

      let payload: ArrayBuffer;
      if (event.data instanceof Blob) {
        payload = await event.data.arrayBuffer();
      } else {
        payload = event.data as ArrayBuffer;
      }

      try {
        const decoded = decode(new Uint8Array(payload));
        const normalized = normalizeSnapshot(decoded, textDecoderRef.current!);
        if (normalized) {
          const now = Date.now() * 1e6;
          const latencyNs = Math.max(0, now - normalized.ts);
          setLatency(latencyNs / 1e6);
          setSnapshot(normalized);
        }
      } catch (err) {
        console.error('MessagePack decode error:', err);
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

function normalizeSnapshot(
  decoded: unknown,
  decoder: TextDecoder
): OrderbookSnapshot | null {
  if (!decoded) return null;

  let value = decoded as any;
  if (value instanceof Map) {
    const obj: Record<string, any> = {};
    for (const [key, val] of value.entries()) {
      if (key instanceof Uint8Array) {
        obj[decoder.decode(key)] = val;
      } else {
        obj[String(key)] = val;
      }
    }
    value = obj;
  }

  if (!value || typeof value !== 'object') return null;
  if (!('ts' in value) || !('bids' in value) || !('asks' in value)) return null;

  return value as OrderbookSnapshot;
}
