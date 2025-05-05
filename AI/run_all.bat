@echo off
rem ── 전역 환경 변수 설정 ──
set OLLAMA_KEEP_ALIVE=-1
set OLLAMA_HOST=0.0.0.0
set OLLAMA_DEBUG=1
set CUDA_VISIBLE_DEVICES=0

rem ── Ollama 경로 찾기 ──
for /f "tokens=*" %%i in ('where ollama') do set OLLAMA_PATH=%%i

rem ── GPU 확인 및 Ollama 실행 ──
start "Ollama GPU Run" cmd /k "nvidia-smi && echo Ollama path: %OLLAMA_PATH% && "%OLLAMA_PATH%" run gemma3"

rem ── 서버 실행 ──
cd /d server
call run_server.bat
