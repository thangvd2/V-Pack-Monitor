@echo off
title V-Pack Monitor Server
echo =====================================
echo  KHOI DONG V-PACK MONITOR SERIES
echo =====================================
echo Dang bat may chu Backend va Web...

if not exist "recordings" mkdir recordings

REM Start server in background
start /B python -m uvicorn api:app --host 0.0.0.0 --port 8001

echo Doi may chu khoi dong...
timeout /t 3 /nobreak >nul

echo Da mo trinh duyet!
start http://localhost:8001

echo Nhan phim bat ky hoac tat cua so nay de ngung may chu.
pause
taskkill /F /IM python.exe /T
