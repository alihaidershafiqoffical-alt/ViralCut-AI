# ViralCut One-Click Local Launcher for Windows
Write-Host "======================================================" -ForegroundColor Cyan
Write-Host "       STARTING VIRALCUT LOCAL DEVELOPMENT SUITE       " -ForegroundColor Cyan
Write-Host "======================================================" -ForegroundColor Cyan

$RootPath = Split-Path -Parent $MyInvocation.MyCommand.Path
$RedisPath = Join-Path $RootPath "redis\redis-server.exe"
$BackendPath = Join-Path $RootPath "backend"
$PythonPath = Join-Path $BackendPath "venv\Scripts\python.exe"
$FrontendPath = Join-Path $RootPath "frontend"

# 1. Start Redis
Write-Host "[1/4] Starting Redis Server on port 6379..." -ForegroundColor Yellow
Start-Process -FilePath $RedisPath -ArgumentList "--port 6379" -WindowStyle Minimized

# 2. Start Celery Solo Worker
Write-Host "[2/4] Starting Celery Background Worker (Solo pool for Windows)..." -ForegroundColor Yellow
Start-Process -FilePath $PythonPath -ArgumentList "-m celery -A app.core.celery_app.celery_app worker -l info -P solo" -WorkingDirectory $BackendPath

# 3. Start FastAPI Backend
Write-Host "[3/4] Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Yellow
Start-Process -FilePath $PythonPath -ArgumentList "-m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -WorkingDirectory $BackendPath

# 4. Start Next.js Frontend
Write-Host "[4/4] Starting Next.js Frontend on http://localhost:3000..." -ForegroundColor Yellow
Start-Process -FilePath "npm.cmd" -ArgumentList "run dev" -WorkingDirectory $FrontendPath

Write-Host "======================================================" -ForegroundColor Green
Write-Host " All 4 services started successfully!" -ForegroundColor Green
Write-Host " -> Frontend: http://localhost:3000" -ForegroundColor Green
Write-Host " -> Backend:  http://127.0.0.1:8000/docs" -ForegroundColor Green
Write-Host "======================================================" -ForegroundColor Green
