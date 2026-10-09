@echo off
title Scrcpy - View-Only Monitor Mode
echo ========================================================
echo   Starting Scrcpy in View-Only Monitor Mode
echo   - Mouse and Keyboard input to device is DISABLED
echo   - Safe for watching videos, monitoring, or presentations
echo ========================================================
cd /d "%~dp0\.."
scrcpy.exe --no-control --video-bit-rate=8M --max-fps=60 %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Scrcpy exited with error code %ERRORLEVEL%.
    pause
)
