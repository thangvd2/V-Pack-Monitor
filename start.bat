@echo off
setlocal EnableDelayedExpansion
title V-Pack Monitor Server
echo =====================================
echo  KHOI DONG V-PACK MONITOR SERIES
echo =====================================
echo Dang bat may chu Backend va Web...

if not exist "recordings" mkdir recordings

start /B python -m uvicorn api:app --host 0.0.0.0 --port 8001
set SERVER_PID=!errorlevel!

echo Doi may chu khoi dong...
timeout /t 3 /nobreak >nul

echo Da mo trinh duyet!
start http://localhost:8001

echo Nhan phim bat ky hoac tat cua so nay de ngung may chu.
pause >nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8001 ^| findstr LISTENING') do (
    taskkill /F /PID %%a 2>nul
)
endlocal
