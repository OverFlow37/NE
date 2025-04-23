@echo off
setlocal

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