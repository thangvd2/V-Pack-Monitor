@echo off
title V-Pack Monitor Server
echo ===========================================
echo  DANG KHOI DONG V-PACK MONITOR SERIES
echo ===========================================

REM 1. ADD LOCAL FFMPEG TO PATH TEMPORARILY
if exist "bin\ffmpeg\bin" (
    set PATH=%CD%\bin\ffmpeg\bin;%PATH%
)

if not exist "recordings" mkdir recordings

REM 2. ACTIVATE VIRTUAL ENV
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo LOI: Khong tim thay moi truong ao venv!
    echo Vui long chay install_windows.bat truoc.
    echo.
    pause
    exit /b 1
)

REM 3. START SERVER IN BACKGROUND
echo Dang bat may chu Backend va Web...
start /B python -m uvicorn api:app --host 0.0.0.0 --port 8001
if %errorLevel% neq 0 (
    echo.
    echo LOI: Khong khoi dong duoc server!
    echo Kiem tra Python va thu vien da duoc cai dat chua.
    echo.
    pause
    exit /b 1
)

echo Doi may chu khoi dong...
timeout /t 3 /nobreak >nul

REM 4. START CHROME IN KIOSK APP MODE
echo Dang mo Giao Dien V-Pack Monitor...
start chrome.exe --app=http://localhost:8001

echo Giao dich dang dien ra. Nhan tat bang nay de ngung he thong!
pause
taskkill /F /IM python.exe /T
