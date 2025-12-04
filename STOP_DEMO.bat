@echo off
title DegreePath Tutor - Stopping...
color 0C

echo.
echo ============================================================
echo   DegreePath Tutor - Stopping All Services
echo ============================================================
echo.

echo Stopping Python processes...
taskkill /F /IM python.exe 2>nul
if %errorlevel%==0 (
    echo [OK] Python processes stopped
) else (
    echo [--] No Python processes found
)

echo Stopping Node processes...
taskkill /F /IM node.exe 2>nul
if %errorlevel%==0 (
    echo [OK] Node processes stopped
) else (
    echo [--] No Node processes found
)

echo.
echo ============================================================
echo   All services stopped!
echo ============================================================
echo.
echo Press any key to close...
pause > nul
