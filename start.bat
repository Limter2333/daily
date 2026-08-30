@echo off
chcp 65001 >nul

echo ============================================================
echo           Daily Briefing System Startup Script
echo ============================================================
echo.

REM Check Python
echo [1/6] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed
    pause
    exit /b 1
)
echo OK: Python found

REM Check Node.js
echo [2/6] Checking Node.js...
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed
    pause
    exit /b 1
)
echo OK: Node.js found

REM Install Python dependencies
echo [3/6] Installing Python dependencies...
pip install -r requirements.txt -q

REM Install frontend dependencies
echo [4/6] Installing frontend dependencies...
cd frontend
call npm install --silent
cd ..

REM Create directories
if not exist data mkdir data
if not exist logs mkdir logs
if not exist logs\backend mkdir logs\backend
if not exist logs\frontend mkdir logs\frontend

REM Check .env file
echo [5/6] Checking configuration...
if not exist .env (
    echo WARNING: .env file not found, creating from template...
    copy .env.example .env >nul
    echo Please edit .env file and add your API key
    echo.
    echo Example:
    echo   AI_API_KEY=sk-your-api-key-here
    echo   AI_MODEL=gpt-4o
    echo   AI_BASE_URL=https://api.xiaomimimo.com/v1
    echo.
    pause
)

echo [6/6] Starting services...
echo.

REM Stop existing backend processes on port 8002
echo Checking for existing backend processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8002 ^| findstr LISTENING') do (
    echo Stopping backend process %%a...
    taskkill /PID %%a /F >nul 2>&1
)

REM Stop existing frontend processes on port 5173
echo Checking for existing frontend processes...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173 ^| findstr LISTENING') do (
    echo Stopping frontend process %%a...
    taskkill /PID %%a /F >nul 2>&1
)

REM Wait for processes to stop
timeout /t 2 /nobreak >nul

REM Start backend
echo Starting backend server...
start "Backend Server" cmd /c "python -m uvicorn backend.main:app --host 0.0.0.0 --port 8002 --reload"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
echo Starting frontend server...
start "Frontend Server" cmd /c "cd frontend && npm run dev"

echo.
echo ============================================================
echo                    System Started!
echo ============================================================
echo.
echo   Frontend:  http://localhost:5173
echo   Backend:   http://localhost:8002
echo   API Docs:  http://localhost:8002/docs
echo.
echo   Logs:
echo     Backend:  logs\backend\
echo     Frontend: logs\frontend\ (browser console)
echo.
echo   To stop: Close the "Backend Server" and "Frontend Server" windows
echo.
echo ============================================================

pause
