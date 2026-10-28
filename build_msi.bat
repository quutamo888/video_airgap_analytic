@echo off
setlocal
cd /d "%~dp0"

echo ========================================================
echo   Building Video Dead Air Cutter Windows MSI Installer
echo ========================================================

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installer\build_msi.ps1"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] MSI Build failed with code %ERRORLEVEL%.
    pause
    exit /b %ERRORLEVEL%
)

echo.
pause
