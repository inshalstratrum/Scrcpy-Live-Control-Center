@echo off
setlocal enabledelayedexpansion
title Scrcpy - Automatic Wireless Connect
echo ========================================================
echo   Configuring and Connecting Scrcpy Over Wi-Fi
echo ========================================================
cd /d "%~dp0\.."

echo [*] Checking connected USB devices...
.\adb.exe get-state >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] No device detected via USB. Please connect USB cable once to initialize Wi-Fi.
    echo If you already know your device IP, enter it below:
    set /p DEVICE_IP="Enter Device IP (e.g. 192.168.1.4): "
) else (
    echo [*] Detecting device Wi-Fi IP address...
    for /f "tokens=*" %%i in ('powershell -Command "$out = .\adb.exe shell ip -f inet addr show wlan0; if ($out -match 'inet\s+(\d+\.\d+\.\d+\.\d+)') { $matches[1] }"') do (
        set DEVICE_IP=%%i
    )
)

if "%DEVICE_IP%"=="" (
    echo [!] Could not auto-detect Wi-Fi IP. Please ensure Wi-Fi is enabled on your phone.
    set /p DEVICE_IP="Enter Device IP manually: "
)

echo [*] Device IP: %DEVICE_IP%
echo [*] Enabling ADB over TCP/IP port 5555...
.\adb.exe tcpip 5555

timeout /t 2 >nul
echo [*] Connecting to %DEVICE_IP%:5555...
.\adb.exe connect %DEVICE_IP%:5555

echo.
echo [*] Launching Scrcpy wirelessly...
scrcpy.exe -s %DEVICE_IP%:5555 --stay-awake --video-bit-rate=8M --max-fps=60 %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] Wireless session ended or failed.
    pause
)
