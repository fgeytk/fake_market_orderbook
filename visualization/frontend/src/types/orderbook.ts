export interface OrderbookSnapshot {
  ts: number;
  seq: number;
  bids: [number, number][];  // [price, size]
  asks: [number, number][];
}

export interface L3Message {
  msg_type: string;
  timestamp: number;
  order_id?: number;
  side?: string;
  price_tick?: number;
  price?: number;
  quantity?: number;
  maker_id?: number;
  aggressor_side?: string;
  cancelled_quantity?: number;
}

export interface Metrics {
  latency: number;
  seq: number;
  fps: number;
  spread: number;
  midPrice: number;
  imbalance: number;
  msgPerSec: number;
}
