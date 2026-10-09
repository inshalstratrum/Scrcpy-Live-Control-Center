@echo off
title Scrcpy - Audio-Only Forwarding
echo ========================================================
echo   Starting Scrcpy Audio-Only Mode
echo   - Video mirroring is disabled (no window)
echo   - Streams phone sound/music directly to PC speakers
echo ========================================================
cd /d "%~dp0\.."
scrcpy.exe --no-video --audio-codec=opus %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Scrcpy audio stream exited with error code %ERRORLEVEL%.
    pause
)
