@echo off
setlocal EnableDelayedExpansion
title V-Pack Monitor Server
echo ===========================================
echo  V-PACK MONITOR - KHOI DONG HE THONG
echo ===========================================

if exist "bin\ffmpeg\bin" set PATH=%CD%\bin\ffmpeg\bin;%PATH%

if not exist "recordings" mkdir recordings

REM === Check if frontend needs rebuild ===
if exist "web-ui\dist\index.html" goto :frontend_ok
echo [Frontend] Dang build giao dien Web lan dau...
if not exist "web-ui\node_modules" (
    echo [Frontend] Cai dat thu vien npm...
    pushd web-ui
    call npm install
    if !errorLevel! neq 0 (
        echo LOI: npm install that bai! Kiem tra Node.js.
        popd
        pause
        exit /b 1
    )
    popd
)
pushd web-ui
call npm run build
if !errorLevel! neq 0 (
    echo LOI: Build frontend that bai!
    popd
    pause
    exit /b 1
)
popd
echo [Frontend] Build hoan tat!
:frontend_ok

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
