@echo off
title DegreePath Tutor - Starting...
color 0A

echo.
echo ============================================================
echo   DegreePath Tutor - 1-Click Demo Launcher
echo ============================================================
echo.

:: Set paths
set PROJECT_DIR=%~dp0
set VENV_DIR=%PROJECT_DIR%degreepath_tutor_DEMO
set NODE_PATH=C:\Program Files\nodejs

:: Check if virtual environment exists
if not exist "%VENV_DIR%\Scripts\activate.bat" (
    echo [ERROR] Virtual environment not found!
    echo Please run: python -m venv degreepath_tutor_DEMO
    pause
    exit /b 1
)

echo [1/4] Activating Python environment...
call "%VENV_DIR%\Scripts\activate.bat"

echo [2/4] Starting Part 1 API (Port 8000)...
start "Part1-API" cmd /k "cd /d %PROJECT_DIR% && call %VENV_DIR%\Scripts\activate.bat && python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000"

:: Wait for Part 1 to initialize
timeout /t 5 /nobreak > nul

echo [3/4] Starting Part 2 API (Port 8001)...
start "Part2-API" cmd /k "cd /d %PROJECT_DIR% && call %VENV_DIR%\Scripts\activate.bat && python -m uvicorn part2.main:app --host 0.0.0.0 --port 8001"

:: Wait for Part 2 to initialize
timeout /t 3 /nobreak > nul

echo [4/4] Starting Frontend (Port 3000)...
start "Frontend" cmd /k "cd /d %PROJECT_DIR%frontend && set PATH=%NODE_PATH%;%%PATH%% && "%NODE_PATH%\node.exe" node_modules\vite\bin\vite.js --host"

:: Wait for frontend to start
timeout /t 3 /nobreak > nul

echo.
echo ============================================================
echo   ALL SERVICES STARTED!
echo ============================================================
echo.
echo   Frontend:  http://localhost:3000
echo   Part 1 API: http://localhost:8000
echo   Part 2 API: http://localhost:8001
echo.
echo   Opening browser in 3 seconds...
echo.
echo   To stop: Close all terminal windows or run STOP_DEMO.bat
echo ============================================================

timeout /t 3 /nobreak > nul

:: Open browser
start http://localhost:3000

echo.
echo Press any key to close this window (services will keep running)...
pause > nul
