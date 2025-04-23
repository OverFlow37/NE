@echo off
setlocal

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
REM  Launch Flask server in a new command window
REM --------------------------------------------------------
start "Flask Server" cmd /k "cd /d %~dp0 && python -u server.py && pause"

REM Wait for server to initialize
timeout /t 2 >nul

@REM REM --------------------------------------------------------
@REM REM  Set CUDA path (if available) or use default
@REM REM --------------------------------------------------------
@REM if defined CUDA_PATH (
@REM     set "PATH=%CUDA_PATH%\bin;%PATH%"
@REM ) else (
@REM     set "PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin;%PATH%"
@REM )

@REM REM Force GPU usage
@REM set OLLAMA_CUDA=1

@REM REM Set Ollama model path (absolute path)
@REM set "OLLAMA_MODELS=%~dp0models"

@REM REM --------------------------------------------------------
@REM REM  Display model path
@REM REM --------------------------------------------------------
@REM echo.
@REM echo ===============================
@REM echo   MODEL DIRECTORY:
@REM for %%I in ("%OLLAMA_MODELS%") do echo   %%~fI
@REM echo ===============================
@REM echo.

REM --------------------------------------------------------
REM  List available Ollama models
REM --------------------------------------------------------
echo [INFO] Starting Ollama...
ollama run gemma3

REM Wait for Ollama to initialize
timeout /t 5 >nul