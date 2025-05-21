@echo off
setlocal

ollama list

REM --------------------------------------------------------
REM  Setup & Activate Python Virtual Environment (venv)
REM --------------------------------------------------------
if not exist "%~dp0venv\Scripts\activate.bat" (
    echo [INFO] Virtual environment not found. Creating venv...
    python -m venv "%~dp0venv"
)

echo [INFO] Activating virtual environment...
call "%~dp0venv\Scripts\activate.bat"

REM --------------------------------------------------------
REM  Install Python dependencies if requirements.txt exists
REM --------------------------------------------------------
if exist "%~dp0requirements.txt" (
    echo [INFO] Installing Python dependencies...
    pip install -r "%~dp0requirements.txt"
)

REM --------------------------------------------------------
REM  Launch Flask server in a new command window with venv activated
REM --------------------------------------------------------
start "Server" cmd /k "cd /d %~dp0 && call venv\Scripts\activate.bat && python -u server.py && pause"

REM Wait a moment for server to spin up
timeout /t 2 >nul
