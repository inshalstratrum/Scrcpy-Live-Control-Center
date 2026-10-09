@echo off
title Scrcpy - Full Interactive Control (UHID Mouse and Keyboard)
echo ========================================================
echo   Starting Scrcpy in Full Interactive Control Mode
echo   - Hardware UHID Simulation Active (Works on Xiaomi/Poco)
echo   - Full PC Mouse and Keyboard Control
echo   - Right-click = Back (powers on screen if off)
echo   - Middle-click = Home
echo   - Press Left-Alt to release mouse cursor to PC
echo ========================================================
cd /d "%~dp0\.."
scrcpy.exe --keyboard=uhid --mouse=uhid --mouse-bind=bhsn:++++ --shortcut-mod=lalt --video-bit-rate=8M --max-fps=60 %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Scrcpy exited with error code %ERRORLEVEL%.
    pause
)
