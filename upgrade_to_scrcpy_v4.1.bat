@echo off
setlocal enabledelayedexpansion
title Scrcpy Upgrade to v4.1
echo ========================================================
echo   Upgrading Scrcpy to v4.1 (SDL3 + Flex Display)
echo ========================================================
cd /d "%~dp0"

echo [*] Downloading scrcpy-win64-v4.1.zip from GitHub...
curl -L -o "scrcpy-win64-v4.1.zip" "https://github.com/Genymobile/scrcpy/releases/download/v4.1/scrcpy-win64-v4.1.zip"

if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Download failed. Please check your internet connection.
    pause
    exit /b 1
)

echo [*] Creating backup folder (backup_v3.3.4)...
if not exist backup_v3.3.4 mkdir backup_v3.3.4
copy /y scrcpy.exe backup_v3.3.4\ >nul
copy /y scrcpy-server backup_v3.3.4\ >nul
copy /y SDL2.dll backup_v3.3.4\ >nul 2>nul
copy /y avcodec-61.dll backup_v3.3.4\ >nul 2>nul
copy /y avformat-61.dll backup_v3.3.4\ >nul 2>nul
copy /y avutil-59.dll backup_v3.3.4\ >nul 2>nul
copy /y swresample-5.dll backup_v3.3.4\ >nul 2>nul

echo [*] Extracting scrcpy v4.1...
powershell -Command "Expand-Archive -Path 'scrcpy-win64-v4.1.zip' -DestinationPath 'temp_v4.1' -Force"

if exist "temp_v4.1\scrcpy-win64-v4.1" (
    copy /y "temp_v4.1\scrcpy-win64-v4.1\*" "." >nul
    rmdir /s /q "temp_v4.1"
    del /f /q "scrcpy-win64-v4.1.zip"
    echo.
    echo ========================================================
    echo   [SUCCESS] Scrcpy successfully updated to v4.1!
    echo ========================================================
    .\scrcpy.exe --version
) else (
    echo [ERROR] Extraction structure was unexpected. Please check temp_v4.1 folder.
)

pause
