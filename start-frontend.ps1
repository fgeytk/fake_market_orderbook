# Quick Start Script for Orderbook Live HFT Frontend

Write-Host "🚀 Starting Orderbook Live - HFT Edition" -ForegroundColor Cyan
Write-Host ""

# Check if Node.js is installed
try {
    $nodeVersion = node --version
    Write-Host "✓ Node.js $nodeVersion detected" -ForegroundColor Green
} catch {
    Write-Host "✗ Node.js not found. Please install from https://nodejs.org/" -ForegroundColor Red
    exit 1
}

Set-Location "visualization\frontend"

# Install dependencies if needed
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Installing dependencies..." -ForegroundColor Yellow
    npm install
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ npm install failed" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🔧 Starting development server..." -ForegroundColor Cyan
Write-Host "   Frontend: http://localhost:3000" -ForegroundColor Blue
Write-Host "   Backend:  http://localhost:8000" -ForegroundColor Blue
Write-Host ""
Write-Host "📡 Make sure the Python backend is running on port 8000" -ForegroundColor Yellow
Write-Host ""

npm run dev
