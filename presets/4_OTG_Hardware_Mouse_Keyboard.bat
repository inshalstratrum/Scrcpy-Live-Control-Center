@echo off
title Scrcpy - Hardware Mouse and Keyboard (UHID)
echo ========================================================
echo   Starting Scrcpy with Hardware UHID Simulation
echo   - Mouse and Keyboard act as physical USB peripherals
echo   - Native phone mouse cursor visible on phone screen
echo   - Best for games or apps blocking virtual inputs
echo ========================================================
cd /d "%~dp0\.."
scrcpy.exe --keyboard=uhid --mouse=uhid --mouse-bind=bhsn:++++ --shortcut-mod=lalt %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Scrcpy exited with error code %ERRORLEVEL%.
    pause
)
