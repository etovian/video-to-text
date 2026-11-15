@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found. Please run:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

echo Starting Video to Text Transcriber...
".venv\Scripts\python.exe" run.py
if errorlevel 1 (
    echo.
    echo Application stopped with an error.
    pause
)
