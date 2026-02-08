# Orderbook Live - HFT Frontend

High-performance React + TypeScript + WebGL orderbook visualization.

## Stack
- **React 18** + TypeScript
- **Vite** (ultra-fast HMR)
- **WebGL** rendering (60+ FPS)
- **Web Workers** (MessagePack decoding)
- **WebSocket** binary stream

## Quick Start

```bash
# Install dependencies
npm install

# Start dev server (http://localhost:3000)
npm run dev

# Build for production
npm run build
```

## Backend Required

Make sure the Python backend is running:

```bash
cd ..
python -m uvicorn visualization.ws_server:app --reload --port 8000
```

## Architecture

```
WebSocket (msgpack)
    ↓
Web Worker (decode)
    ↓
React State
    ↓
WebGL Renderer (60 FPS)
```

## Features

- ✅ 60+ FPS rendering
- ✅ WebGL-accelerated depth chart
- ✅ Real-time metrics (latency, fps, spread, imbalance)
- ✅ Web Worker for non-blocking decode
- ✅ TypeScript type safety
- ✅ Responsive layout

## Performance

- **MessagePack**: Binary protocol, faster than JSON
- **Web Worker**: Decode in background thread
- **WebGL**: GPU-accelerated rendering
- **RequestAnimationFrame**: Smooth 60 FPS
- **SWC**: 20x faster than Babel
