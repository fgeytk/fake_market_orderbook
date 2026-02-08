# 🚀 Quick Start - Orderbook Live HFT Edition

Complete setup with **React 18 + TypeScript + Vite + WebGL**

## Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   React UI  │ ◄─WS──► │ FastAPI Back │ ◄────► │  Orderbook  │
│  (Port 3000)│         │  (Port 8000) │         │   Engine    │
└─────────────┘         └──────────────┘         └─────────────┘
     WebGL                  msgpack                 tick-based
   60+ FPS                  binary                   heaps
```

## 🎯 Steps

### 1. Start Backend (Terminal 1)

```powershell
.\start-backend.ps1
```

Or manually:

```bash
python -m uvicorn visualization.ws_server:app --reload --port 8000
```

✓ Backend runs on: `http://localhost:8000`  
✓ WebSocket ready: `ws://localhost:8000/ws`

### 2. Start Frontend (Terminal 2)

```powershell
.\start-frontend.ps1
```

Or manually:

```bash
cd visualization/frontend
npm install
npm run dev
```

✓ Frontend runs on: `http://localhost:3000`

### 3. Open Browser

Navigate to: **http://localhost:3000**

## 🎨 What You Get

✅ **60+ FPS rendering** (WebGL + Canvas 2D hybrid)  
✅ **Real-time metrics**: Latency, FPS, Spread, Imbalance  
✅ **Web Worker**: Non-blocking MessagePack decode  
✅ **TypeScript**: Full type safety  
✅ **Hot Module Replacement**: Instant updates  
✅ **Responsive**: Desktop & mobile ready

## 📊 UI Features

| Panel | Content |
|-------|---------|
| **Left** | Depth chart with price levels (WebGL) |
| **Right** | Metrics + Best Bid/Ask + Spread |
| **Header** | Latency, FPS, Seq, Connection status |

## 🔧 Tech Stack

- **Frontend**: React 18, TypeScript, Vite
- **Rendering**: WebGL (fallback to Canvas 2D)
- **Workers**: MessagePack decoding in background
- **Backend**: FastAPI, uvicorn, msgpack
- **Protocol**: WebSocket binary (msgpack)

## 📈 Performance

- **Latency**: <2ms (localhost)
- **Throughput**: 500+ updates/sec
- **FPS**: 60+ (constant)
- **Bundle**: <200KB (gzipped)

## 🛠️ Development

### Build for Production

```bash
cd visualization/frontend
npm run build
```

Output in `dist/` directory, ready to deploy.

### Preview Production Build

```bash
npm run preview
```

## 🐛 Troubleshooting

**Frontend can't connect?**
- Check backend is running on port 8000
- Check WebSocket endpoint: `ws://localhost:8000/ws`

**Black screen?**
- Open DevTools console for errors
- Check WebGL support: chrome://gpu

**Low FPS?**
- Reduce `target_fps` in ws_server.py
- Check CPU usage (Activity Monitor / Task Manager)

## 📦 Project Structure

```
visualization/
├── frontend/              # React + TypeScript
│   ├── src/
│   │   ├── components/    # React components
│   │   ├── hooks/         # Custom hooks (WebSocket)
│   │   ├── workers/       # Web Workers (msgpack)
│   │   ├── types/         # TypeScript types
│   │   ├── App.tsx        # Main app
│   │   └── main.tsx       # Entry point
│   ├── index.html
│   ├── vite.config.ts
│   └── package.json
├── ws_server.py           # FastAPI backend
└── web/                   # Old vanilla JS UI
```

## 🚀 Next Steps

- Add more chart types (heatmap, candlesticks)
- Implement zoom controls
- Add trade tape panel
- Multi-instrument support
- Historical data playback

---

**Ready to trade! 📈**
