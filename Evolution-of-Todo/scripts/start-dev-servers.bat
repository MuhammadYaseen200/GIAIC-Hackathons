@echo off
REM Development Server Startup Script (Windows)
REM Auto-generated: 2026-02-07

setlocal

set PROJECT_ROOT=E:\M.Y\GIAIC-Hackathons\Evolution-of-Todo

echo ============================================================
echo Evolution of Todo - Development Servers
echo ============================================================

REM Validate working directory
cd /d "%PROJECT_ROOT%"
if errorlevel 1 (
    echo [ERROR] Failed to change to project directory
    exit /b 3
)

echo [OK] Working directory: %CD%
echo.

REM Test database connection
echo Testing Neon Database Connection...
cd "%PROJECT_ROOT%\phase-3-chatbot\backend"
uv run python test_connections.py >nul 2>&1
if errorlevel 1 (
    echo [ERR] Database connection failed
    echo Run: cd phase-3-chatbot\backend ^&^& uv run python test_connections.py
    exit /b 1
)
echo [OK] Database connection successful
echo.

echo ============================================================
echo Starting Backend Server (FastAPI)
echo ============================================================
echo [INFO] Backend URL: http://localhost:8000
echo [INFO] API Docs: http://localhost:8000/docs
echo [INFO] Opening in new window...
echo.

REM Start backend in new window
start "Backend - FastAPI" cmd /k "cd /d %PROJECT_ROOT%\phase-3-chatbot\backend && uv run uvicorn app.main:app --reload --port 8000"

REM Wait for backend to start
echo Waiting for backend to be ready...
timeout /t 5 /nobreak >nul
echo.

echo ============================================================
echo Starting Frontend Server (Next.js)
echo ============================================================
echo [INFO] Frontend URL: http://localhost:3000
echo [INFO] Opening in new window...
echo.

REM Start frontend in new window
start "Frontend - Next.js" cmd /k "cd /d %PROJECT_ROOT%\phase-3-chatbot\frontend && pnpm dev"

echo.
echo ============================================================
echo Servers Running
echo ============================================================
echo [OK] Backend:  http://localhost:8000
echo [OK] Frontend: http://localhost:3000
echo.
echo Close the server windows to stop the servers.
echo ============================================================
echo.

pause
