@echo off
setlocal EnableDelayedExpansion
title V-Pack Monitor Server
echo ===========================================
echo  V-PACK MONITOR - KHOI DONG HE THONG
echo ===========================================

if exist "bin\ffmpeg\bin" set PATH=%CD%\bin\ffmpeg\bin;%PATH%

if not exist "recordings" mkdir recordings

if not exist "venv\Scripts\activate.bat" goto :no_venv
goto :venv_ok

:no_venv
echo.
echo LOI: Khong tim thay moi truong ao venv!
echo Vui long chay install_windows.bat truoc.
echo.
pause
exit /b 1

:venv_ok
if not exist "bin\mediamtx\mediamtx.exe" goto :skip_mtx
echo Dang khoi dong MediaMTX (WebRTC Live View)...
start "MediaMTX" /B "bin\mediamtx\mediamtx.exe" "bin\mediamtx\mediamtx.yml"
ping -n 3 127.0.0.1 >nul

:skip_mtx
call venv\Scripts\activate.bat

echo Dang khoi dong may chu Python...
start "V-Pack API" /B python -m uvicorn api:app --host 0.0.0.0 --port 8001
ping -n 5 127.0.0.1 >nul

echo Dang mo giao dien V-Pack Monitor...
start "" chrome.exe --app=http://localhost:8001 2>nul
if !errorLevel! neq 0 (
    start "" http://localhost:8001
)

echo.
echo ===========================================
echo  He thong dang chay. Nhan phim bat ky de tat.
echo ===========================================
pause >nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
taskkill /F /IM mediamtx.exe /T 2>nul
endlocal
