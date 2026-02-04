const canvas = document.getElementById("depth");
const ctx = canvas.getContext("2d");
const latencyEl = document.getElementById("latency");
const seqEl = document.getElementById("seq");
const fpsEl = document.getElementById("fps");
const statusEl = document.getElementById("ws-status");
const bestBidEl = document.getElementById("best-bid");
const bestAskEl = document.getElementById("best-ask");

let lastFrame = performance.now();
let frameCount = 0;
let lastFpsUpdate = performance.now();

let latest = null;

function resizeCanvas() {
  const ratio = window.devicePixelRatio || 1;
  const { width, height } = canvas.getBoundingClientRect();
  canvas.width = Math.floor(width * ratio);
  canvas.height = Math.floor(height * ratio);
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
}

window.addEventListener("resize", resizeCanvas);
resizeCanvas();

function drawDepth(snapshot) {
  const { bids, asks } = snapshot;
  const width = canvas.clientWidth;
  const height = canvas.clientHeight;

  ctx.clearRect(0, 0, width, height);
  ctx.fillStyle = "#0b111b";
  ctx.fillRect(0, 0, width, height);

  const midX = width / 2;
  const barHeight = Math.max(4, height / (Math.max(bids.length, asks.length) + 4));

  const maxSize = Math.max(
    1,
    ...bids.map((b) => b[1]),
    ...asks.map((a) => a[1])
  );

  const scale = (width * 0.42) / maxSize;

  ctx.font = "12px 'Segoe UI'";
  ctx.fillStyle = "#7b8796";
  ctx.fillText("BID", midX - 40, 16);
  ctx.fillText("ASK", midX + 10, 16);

  bids.forEach((level, idx) => {
    const [price, size] = level;
    const barWidth = size * scale;
    const y = 30 + idx * barHeight;

    ctx.fillStyle = "rgba(46, 204, 113, 0.8)";
    ctx.fillRect(midX - barWidth, y, barWidth - 2, barHeight - 2);

    ctx.fillStyle = "#c7d2e0";
    ctx.fillText(`$${price.toFixed(2)}`, midX - barWidth - 72, y + barHeight * 0.7);
    ctx.fillText(`${size}`, midX - barWidth - 16, y + barHeight * 0.7);
  });

  asks.forEach((level, idx) => {
    const [price, size] = level;
    const barWidth = size * scale;
    const y = 30 + idx * barHeight;

    ctx.fillStyle = "rgba(231, 76, 60, 0.8)";
    ctx.fillRect(midX + 2, y, barWidth, barHeight - 2);

    ctx.fillStyle = "#c7d2e0";
    ctx.fillText(`$${price.toFixed(2)}`, midX + barWidth + 8, y + barHeight * 0.7);
    ctx.fillText(`${size}`, midX + barWidth + 72, y + barHeight * 0.7);
  });
}

function updateStats(snapshot) {
  if (!snapshot) return;
  const now = performance.now();
  frameCount += 1;
  if (now - lastFpsUpdate > 1000) {
    const fps = Math.round((frameCount * 1000) / (now - lastFpsUpdate));
    fpsEl.textContent = `${fps}`;
    frameCount = 0;
    lastFpsUpdate = now;
  }

  if (snapshot.ts) {
    const latencyMs = Math.max(0, (Date.now() * 1e6 - snapshot.ts) / 1e6);
    latencyEl.textContent = `${latencyMs.toFixed(1)} ms`;
  }
  if (snapshot.seq !== undefined) {
    seqEl.textContent = `${snapshot.seq}`;
  }

  const bestBid = snapshot.bids?.[0];
  const bestAsk = snapshot.asks?.[0];
  if (bestBid) {
    const notionalBid = bestBid[0] * bestBid[1];
    bestBidEl.textContent = `$${bestBid[0].toFixed(2)} × ${bestBid[1]} = $${notionalBid.toFixed(2)}`;
  } else {
    bestBidEl.textContent = "—";
  }

  if (bestAsk) {
    const notionalAsk = bestAsk[0] * bestAsk[1];
    bestAskEl.textContent = `$${bestAsk[0].toFixed(2)} × ${bestAsk[1]} = $${notionalAsk.toFixed(2)}`;
  } else {
    bestAskEl.textContent = "—";
  }
}

function renderLoop() {
  if (latest) {
    drawDepth(latest);
    updateStats(latest);
    latest = null;
  }
  lastFrame = performance.now();
  requestAnimationFrame(renderLoop);
}

function connect() {
  const wsUrl = `ws://${window.location.host.replace(/:\d+$/, ":8000")}/ws`;
  const ws = new WebSocket(wsUrl);
  ws.binaryType = "arraybuffer";

  ws.addEventListener("open", () => {
    statusEl.textContent = "connected";
    statusEl.style.color = "#2ecc71";
  });

  ws.addEventListener("close", () => {
    statusEl.textContent = "disconnected";
    statusEl.style.color = "#e74c3c";
    setTimeout(connect, 1000);
  });

  ws.addEventListener("message", (event) => {
    if (!event.data) return;
    try {
      const decoded = msgpack.decode(new Uint8Array(event.data));
      latest = decoded;
    } catch (err) {
      console.error("Decode error", err);
    }
  });
}

renderLoop();
connect();
