@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo   Building Standalone Video Dead Air Cutter (.exe)
echo ========================================================

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_build.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Build failed with code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [SUCCESS] Build finished!
echo Output folder: dist\VideoDeadAirCutter
echo You can zip and send "dist\VideoDeadAirCutter" to any PC.
pause
