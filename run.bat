@echo off
setlocal
cd /d "%~dp0"

where uv >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 'uv' is not installed or not found in PATH.
    echo Install uv: powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    pause
    exit /b 1
)

where ffmpeg >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [ERROR] 'ffmpeg' is not found in PATH.
    echo Install ffmpeg: winget install Gyan.FFmpeg
    pause
    exit /b 1
)

echo Starting Video Dead Air Cutter using uv...
uv run python main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
