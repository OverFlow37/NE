@echo off
setlocal enabledelayedexpansion

echo [INFO] Starting AI game launcher...

REM Ollama check
echo [INFO] Checking if Ollama is running...
ollama list > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Ollama is not running. Please start Ollama first.
    pause
    exit /b 1
)
echo [INFO] Ollama is running correctly.

REM Change to ai_server/server directory
cd /d "%~dp0ai_server\server"

REM Delete server_ready.txt file if exists
if exist "server_ready.txt" (
    del /f /q "server_ready.txt"
)

REM Check and activate venv
if not exist "venv\Scripts\activate.bat" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

echo [INFO] Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements if available
if exist "requirements.txt" (
    echo [INFO] Installing required packages...
    pip install -r requirements.txt
)

REM Run prepare_server.py
echo [INFO] Running model preparation and server startup...
python prepare_server.py

REM Check server initialization
echo [INFO] Waiting for server initialization...
set MAX_WAIT=3600
set WAIT_TIME=0
set INTERVAL=5

:CHECK_SERVER
timeout /t %INTERVAL% /nobreak > nul
set /a WAIT_TIME+=%INTERVAL%

REM Check for server_ready.txt file
if exist "server_ready.txt" (
    echo [INFO] Server has been fully initialized.
    goto SERVER_RUNNING
)

echo [INFO] Waiting for server initialization... %WAIT_TIME%/%MAX_WAIT% seconds

if %WAIT_TIME% lss %MAX_WAIT% (
    goto CHECK_SERVER
) else (
    echo [ERROR] Server initialization timeout (%MAX_WAIT% seconds).
    echo [ERROR] Please check server logs.
    pause
    exit /b 1
)

:SERVER_RUNNING
echo [INFO] Server is running properly.

REM Return to original directory
cd /d "%~dp0"

REM Start the game and cleanup batch in background (hidden)
echo [INFO] Starting game and closing this window...
start "" /min RunGameAndCleanup.bat

REM Exit immediately
exit
