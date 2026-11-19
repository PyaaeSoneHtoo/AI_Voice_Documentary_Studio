@echo off
title AI Voice Documentary Studio
echo =========================================================
echo       AI Voice Documentary Studio (Windows Launcher)
echo   Powered by FreeLLMAPI (Tokens) and VoiceStudio (Voice)
echo =========================================================
echo.

cd /d "%~dp0"

echo [1/2] Checking Python environment...
python -c "import streamlit, PIL, requests; print('Core dependencies satisfied.')"
if %errorlevel% neq 0 (
    echo [!] Installing required Python packages...
    pip install -r requirements.txt
)

echo [2/2] Launching AI Voice Documentary Studio Web App...
streamlit run app.py --server.port 8501 --server.headless false

pause
