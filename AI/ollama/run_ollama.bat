@echo off
setlocal

REM CUDA_PATH 환경변수 확인 및 bin 폴더 우선 지정
if defined CUDA_PATH (
    set "PATH=%CUDA_PATH%\bin;%PATH%"
) else (
    set "PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v11.8\bin;%PATH%"
)



REM GPU 강제
set OLLAMA_CUDA=1

REM 모델 경로 명시 (상대 경로 오류 방지)
set "OLLAMA_MODELS=%~dp0models"


REM ----------------------------------------
REM  모델 경로(절대경로) 출력
REM ----------------------------------------
echo.
echo ===============================
echo   MODELS PATH:
for %%I in ("%OLLAMA_MODELS%") do echo   %%~fI
echo ===============================
echo.



REM ----------------------------------------
REM  모델 목록 출력
REM ----------------------------------------
echo.
echo ===============================
echo   usable Ollama model list
echo ===============================
"%~dp0ollama.exe" list

REM ----------------------------------------
REM  기본 모델 실행 (필요 시 이름 변경)
REM ----------------------------------------
echo.
echo ===============================
echo   model run gemma3
echo ===============================
"%~dp0ollama.exe" run gemma3

pause
