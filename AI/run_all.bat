@REM REM current ollama.exe terminate
@REM taskkill /IM ollama.exe /F >nul 2>&1

@REM REM env setting
@REM set OLLAMA_KEEP_ALIVE=-1
@REM set CUDA_VISIBLE_DEVICES=0

@REM rem ── Ollama path ──
@REM for /f "tokens=*" %%i in ('where ollama') do set OLLAMA_PATH=%%i

rem ── run ──

@REM rem ── GPU check Ollama run ──
@REM cmd /c "nvidia-smi && "%OLLAMA_PATH%" run gemma3"


cd /d server
call run_server.bat