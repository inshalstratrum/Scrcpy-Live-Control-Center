@echo off
title Scrcpy - Mobile Camera as Webcam (30 FPS True Color)
echo ========================================================
echo   Starting Scrcpy Camera Stream Mode (Native 30 FPS)
echo   - Camera ID 0 (Rear Main Camera - True Exposure & Colors)
echo   - Usable in OBS, Discord, Zoom, etc.
echo ========================================================
cd /d "%~dp0\.."
scrcpy.exe --video-source=camera --camera-id=0 --camera-size=1920x1080 --camera-fps=30 %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Scrcpy camera stream exited with error code %ERRORLEVEL%.
    pause
)
