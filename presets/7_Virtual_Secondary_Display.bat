@echo off
title Scrcpy - Virtual Secondary Display
echo ========================================================
echo   Starting Virtual Secondary Display Mode (Android 13+)
echo   - Creates an independent virtual display on your phone
echo   - Functions like a second monitor for your Android apps
echo ========================================================
cd /d "%~dp0\.."
scrcpy.exe --new-display=1920x1080/320 %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Scrcpy virtual display exited with error code %ERRORLEVEL%.
    pause
)
