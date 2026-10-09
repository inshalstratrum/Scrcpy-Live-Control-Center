@echo off
title Scrcpy Live Control Center
set "SCRIPT_DIR=%~dp0"

echo ========================================================
echo   Scrcpy Live Control Center v4.1 (Universal Hero)
echo ========================================================
echo Launching application...

cd /d "%TEMP%"

where pythonw >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" pythonw "%SCRIPT_DIR%control_center.py"
    exit /b 0
)

where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    start "" python "%SCRIPT_DIR%control_center.py"
    exit /b 0
)

if exist "C:\Python314\pythonw.exe" (
    start "" "C:\Python314\pythonw.exe" "%SCRIPT_DIR%control_center.py"
    exit /b 0
)

if exist "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python312\pythonw.exe" "%SCRIPT_DIR%control_center.py"
    exit /b 0
)

if exist "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe" (
    start "" "%LOCALAPPDATA%\Programs\Python\Python311\pythonw.exe" "%SCRIPT_DIR%control_center.py"
    exit /b 0
)

echo [ERROR] Python was not found on PATH or standard directories.
echo Please ensure Python 3.10+ is installed and on PATH.
pause
