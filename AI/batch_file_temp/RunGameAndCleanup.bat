@echo off
setlocal enabledelayedexpansion

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM OhMaiGod.exe 직접 실행
start "" "NewEden.exe"

REM 게임 프로세스가 종료되었는지 확인하는 루프
:CHECK_GAME
timeout /t 5 /nobreak > nul
tasklist | find /i "NewEden.exe" > nul
if %errorlevel% equ 0 (
    goto CHECK_GAME
) else (
    goto CLEANUP
)

:CLEANUP
REM 게임이 종료되면 서버 프로세스 종료
taskkill /f /fi "WINDOWTITLE eq Server" > nul 2>&1
taskkill /f /fi "WINDOWTITLE eq python" > nul 2>&1
taskkill /f /im python.exe > nul 2>&1

REM 종료
exit 