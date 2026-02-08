# Start Python backend server for Orderbook Live

Write-Host "Starting Python WebSocket Backend" -ForegroundColor Cyan
Write-Host ""

$venvPython = "C:/Users/titou/Music/IA/.venv/Scripts/python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Python venv not found at $venvPython" -ForegroundColor Red
    exit 1
}

Write-Host "Starting FastAPI server on port 8000..." -ForegroundColor Cyan
Write-Host "WebSocket: ws://localhost:8000/ws" -ForegroundColor Blue
Write-Host "Health:    http://localhost:8000/health" -ForegroundColor Blue
Write-Host ""

& $venvPython -m uvicorn visualization.ws_server:app --reload --host 0.0.0.0 --port 8000
