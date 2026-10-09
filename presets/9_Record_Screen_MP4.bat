@echo off
title Scrcpy - Mirror and Record to MP4
echo ========================================================
echo   Starting Scrcpy with Screen Recording
echo   - Video and Audio will be saved into 'recordings' folder
echo   - Close the scrcpy window to finish and save recording
echo ========================================================
cd /d "%~dp0\.."

if not exist recordings mkdir recordings

for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set TIMESTAMP=%datetime:~0,8%_%datetime:~8,6%
set OUTFILE=recordings\recording_%TIMESTAMP%.mp4

echo [*] Saving recording to: %OUTFILE%
echo.

scrcpy.exe --record="%OUTFILE%" --record-format=mp4 --video-bit-rate=12M --max-fps=60 %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Scrcpy exited with error code %ERRORLEVEL%.
    pause
) else (
    echo.
    echo [*] Recording saved successfully to: %OUTFILE%
    timeout /t 3
)
