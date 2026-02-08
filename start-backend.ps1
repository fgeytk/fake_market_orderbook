# Start Python backend server for Orderbook Live

Write-Host "🐍 Starting Python WebSocket Backend" -ForegroundColor Cyan
Write-Host ""

# Check Python
try {
    $pythonVersion = python --version
    Write-Host "✓ $pythonVersion detected" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "🔧 Starting FastAPI server on port 8000..." -ForegroundColor Cyan
Write-Host "   WebSocket: ws://localhost:8000/ws" -ForegroundColor Blue
Write-Host "   Health:    http://localhost:8000/health" -ForegroundColor Blue
Write-Host ""

python -m uvicorn visualization.ws_server:app --reload --host 0.0.0.0 --port 8000
