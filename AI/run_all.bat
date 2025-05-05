@echo off
rem ── Setting Global Environment Variables ──
set OLLAMA_KEEP_ALIVE=-1
set OLLAMA_HOST=0.0.0.0
set OLLAMA_DEBUG=1
set CUDA_VISIBLE_DEVICES=0

rem ── Ollama path ──
for /f "tokens=*" %%i in ('where ollama') do set OLLAMA_PATH=%%i

rem ── GPU check Ollama run ──
start "Ollama GPU Run" cmd /k "nvidia-smi && echo Ollama path: %OLLAMA_PATH% && "%OLLAMA_PATH%" run gemma3"

rem ── run ──
cd /d server
call run_server.bat
