@echo off
title ViralCut Local Launcher
echo ======================================================
echo        STARTING VIRALCUT LOCAL DEVELOPMENT SUITE       
echo ======================================================

set ROOT_DIR=%~dp0
cd /d "%ROOT_DIR%"

echo [1/4] Starting Redis Server...
start "ViralCut Redis" "%ROOT_DIR%redis\redis-server.exe" --port 6379

echo [2/4] Starting Celery Worker...
start "ViralCut Celery" cmd /k "cd /d %ROOT_DIR%backend && venv\Scripts\python.exe -m celery -A app.core.celery_app.celery_app worker -l info -P solo"

echo [3/4] Starting FastAPI Backend...
start "ViralCut FastAPI" cmd /k "cd /d %ROOT_DIR%backend && venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [4/4] Starting Next.js Frontend...
start "ViralCut Frontend" cmd /k "cd /d %ROOT_DIR%frontend && npm run dev"

echo ======================================================
echo All 4 services launched!
echo Open your browser at: http://localhost:3000
echo ======================================================
pause
