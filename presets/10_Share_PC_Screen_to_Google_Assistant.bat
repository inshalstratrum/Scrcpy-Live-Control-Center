@echo off
title Scrcpy - Share PC Screen to Mobile Google Assistant
echo ========================================================
echo   PC Desktop Screen Share for Mobile Google Assistant
echo   - Streams your PC monitor directly into your phone
echo   - Automatically opens Android browser to the stream
echo   - Allows Google Assistant / Gemini to view PC screen
echo     and converse voice-to-voice about desktop content!
echo ========================================================
cd /d "%~dp0\.."

python pc_to_phone_streamer.py

pause
