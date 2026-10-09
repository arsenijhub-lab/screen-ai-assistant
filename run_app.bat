@echo off
title Screen AI Assistant
cls
echo ========================================================
echo    Screen AI Assistant - Starting...
echo ========================================================
echo.
if exist "ScreenAIAssistant.exe" (
    start "" "ScreenAIAssistant.exe"
    goto :done
)
python desktop_app/main.py
:done
exit
