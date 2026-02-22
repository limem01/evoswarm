@echo off
title EvoSwarm Launcher
echo ============================================
echo   EvoSwarm - Self-Evolving Agent Collective
echo ============================================
echo.

:: Check Docker
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker not found. Install Docker Desktop first.
    pause
    exit /b 1
)

:: Start Neo4j
echo [1/3] Starting Neo4j via Docker...
docker compose up -d neo4j
if errorlevel 1 (
    echo [ERROR] Failed to start Neo4j. Is Docker Desktop running?
    pause
    exit /b 1
)

:: Wait for Neo4j health
echo [*] Waiting for Neo4j to be ready...
:wait_neo4j
timeout /t 3 /nobreak >nul
docker inspect --format="{{.State.Health.Status}}" evoswarm-neo4j 2>nul | findstr "healthy" >nul
if errorlevel 1 goto wait_neo4j
echo [OK] Neo4j is healthy.

:: Start Backend
echo.
echo [2/3] Starting Backend (uvicorn)...
start "EvoSwarm Backend" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload"

:: Give backend a moment
timeout /t 3 /nobreak >nul

:: Start Frontend
echo.
echo [3/3] Starting Frontend (Next.js)...
start "EvoSwarm Frontend" cmd /k "cd /d %~dp0\frontend && npm run dev"

echo.
echo ============================================
echo   EvoSwarm is running!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:3000
echo   Neo4j:    http://localhost:7474
echo ============================================
echo.
echo Press any key to stop all services...
pause >nul

:: Cleanup
echo Stopping services...
docker compose down
taskkill /FI "WINDOWTITLE eq EvoSwarm Backend" /F >nul 2>&1
taskkill /FI "WINDOWTITLE eq EvoSwarm Frontend" /F >nul 2>&1
echo Done.
