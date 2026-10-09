@echo off
title Scrcpy - Screen-Off Battery Saver Mode
echo ========================================================
echo   Starting Scrcpy in Screen-Off Battery Saver Mode
echo   - Physical Device Screen is Turned OFF
echo   - Full PC Mouse and Keyboard Control Active (UHID)
echo   - Reduces Phone Battery Drain and Heat
echo   - Right-click = Back (powers on screen if needed)
echo   - Press Left-Alt to release mouse cursor to PC
echo ========================================================
cd /d "%~dp0\.."
scrcpy.exe --turn-screen-off --keyboard=uhid --mouse=uhid --mouse-bind=bhsn:++++ --shortcut-mod=lalt --video-bit-rate=8M --max-fps=60 %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Scrcpy exited with error code %ERRORLEVEL%.
    pause
)
