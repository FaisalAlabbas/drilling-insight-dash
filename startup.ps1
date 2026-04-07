# Drilling Insight Dashboard - Startup Script (Windows PowerShell)
# Run this script to start both backend and frontend servers

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "DRILLING INSIGHT DASHBOARD - STARTUP" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$aiServiceDir = Join-Path $projectRoot "ai_service"
$frontendDir = $projectRoot

# Check if Python is available
Write-Host "Checking Python installation..." -ForegroundColor Blue
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found. Please install Python 3.8+" -ForegroundColor Red
    exit 1
}

# Install Python dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Blue
$reqFile = Join-Path $aiServiceDir "requirements.txt"
if (Test-Path $reqFile) {
    python -m pip install -q -r $reqFile
    Write-Host "✓ Python dependencies installed" -ForegroundColor Green
}

# Check model
Write-Host "Checking ML model..." -ForegroundColor Blue
$modelPath = Join-Path $aiServiceDir "models\recommendation_model.pkl"
if (Test-Path $modelPath) {
    Write-Host "✓ Model found" -ForegroundColor Green
} else {
    Write-Host "⚠ Model not found. Training may be needed." -ForegroundColor Yellow
}

# Create .env.local if needed
Write-Host "Configuring frontend..." -ForegroundColor Blue
$envFile = Join-Path $frontendDir ".env.local"
if (-not (Test-Path $envFile)) {
    "VITE_AI_BASE_URL=http://localhost:8000" | Out-File -FilePath $envFile -Encoding UTF8
    Write-Host "✓ .env.local created" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "READY TO START SERVERS" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Backend (FastAPI):" -ForegroundColor Cyan
Write-Host "  Location: http://localhost:8000" -ForegroundColor White
Write-Host "  Docs:    http://localhost:8000/docs" -ForegroundColor White
Write-Host ""

Write-Host "Frontend (React):" -ForegroundColor Cyan
Write-Host "  Location: http://localhost:5173" -ForegroundColor White
Write-Host ""

Write-Host "TERMINAL 1 - Start Backend:" -ForegroundColor Yellow
Write-Host "  cd $aiServiceDir" -ForegroundColor White
Write-Host "  python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor White
Write-Host ""

Write-Host "TERMINAL 2 - Start Frontend:" -ForegroundColor Yellow
Write-Host "  cd $frontendDir" -ForegroundColor White
Write-Host "  npm run dev" -ForegroundColor White
Write-Host ""

Write-Host "Starting both servers now..." -ForegroundColor Cyan
Write-Host ""

# Start backend in new window
Write-Host "Launching backend server..." -ForegroundColor Green
$backendCmd = "cd '$aiServiceDir'; python -m uvicorn api:app --reload --host 0.0.0.0 --port 8000"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCmd

# Wait a moment for backend to start
Start-Sleep -Seconds 3

# Start frontend in new window
Write-Host "Launching frontend server..." -ForegroundColor Green
$frontendCmd = "cd '$frontendDir'; npm run dev"
Start-Process powershell -ArgumentList "-NoExit", "-Command", $frontendCmd

Write-Host ""
Write-Host "✓ Both servers launched in new windows" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "  Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""
Write-Host "Opening dashboard in browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 2

# Try to open in browser
try {
    Start-Process "http://localhost:5173"
} catch {
    Write-Host "⚠ Could not open browser automatically. Please visit: http://localhost:5173" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Startup complete! Press any key to close this window." -ForegroundColor Green
$host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") > $null
