@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

set "LOG=%~dp0install_log.txt"
echo [%date% %time%] Bat dau cai dat V-Pack Monitor > "%LOG%"
echo [%date% %time%] Working directory: %CD% >> "%LOG%"

set "PYTHON_CMD=python"

net session >nul 2>&1
if !errorLevel! == 0 (
    echo Kich hoat Quyen Administrator... Thanh Cong.
    echo [%date% %time%] Admin check: OK >> "%LOG%"
) else (
    echo [CANH BAO] Ban chua chay voi Quyen Administrator!
    echo Vui long tat bang nay, Nhan chuot phai vao file install_windows.bat va chon "Run as administrator".
    echo [%date% %time%] Admin check: FAIL >> "%LOG%"
    pause
    exit /b 1
)

echo.
echo ========================================================
echo        CAI DAT V-PACK MONITOR CHO KHO XUONG
echo ========================================================
echo.

REM ============================================
REM 1/7. KIEM TRA VA CAI DAT PYTHON
REM ============================================
echo [1/7] Kiem tra Python...
echo [%date% %time%] Kiem tra Python... >> "%LOG%"

!PYTHON_CMD! --version >nul 2>&1
if !errorLevel! == 0 (
    echo [1/7] Python... Hop le.
    echo [%date% %time%] Python found via "!PYTHON_CMD!" >> "%LOG%"
    goto :python_ok
)

py --version >nul 2>&1
if !errorLevel! == 0 (
    set "PYTHON_CMD=py"
    echo [1/7] Phat hien Python qua lenh "py".
    echo [%date% %time%] Python found via "py" >> "%LOG%"
    goto :python_ok
)

echo [1/7] Khong tim thay Python. Dang tai ve tu dong...
echo [%date% %time%] Downloading Python... >> "%LOG%"
curl -sL -o "%TEMP%\python-installer.exe" "https://www.python.org/ftp/python/3.13.3/python-3.13.3-amd64.exe"
if not exist "%TEMP%\python-installer.exe" (
    echo LOI: Khong tai duoc Python! Kiem tra ket noi Internet.
    echo [%date% %time%] ERROR: Python download failed >> "%LOG%"
    pause
    exit /b 1
)

echo [1/7] Dang cai dat Python (silent, add to PATH)...
echo [%date% %time%] Installing Python silently... >> "%LOG%"
"%TEMP%\python-installer.exe" /quiet InstallAllUsers=1 PrependPath=1 Include_pip=1
del "%TEMP%\python-installer.exe" >nul 2>&1

REM Cap nhat PATH cho session hien tai
set "PATH=%LocalAppData%\Programs\Python\Python313;%LocalAppData%\Programs\Python\Python313\Scripts;%ProgramFiles%\Python313;%ProgramFiles%\Python313\Scripts;%PATH%"

python --version >nul 2>&1
if !errorLevel! == 0 (
    echo [1/7] Cai dat Python... Hoan tat!
    echo [%date% %time%] Python installed OK >> "%LOG%"
    goto :python_ok
)

py --version >nul 2>&1
if !errorLevel! == 0 (
    set "PYTHON_CMD=py"
    echo [1/7] Cai dat Python... Hoan tat! (py launcher)
    echo [%date% %time%] Python installed OK via py >> "%LOG%"
    goto :python_ok
)

echo LOI: Cai dat Python that bai!
echo Vui long cai dat thu cong tu https://www.python.org/downloads/
echo LUU Y: Nho check "Add Python to PATH" khi cai dat!
echo [%date% %time%] ERROR: Python install failed >> "%LOG%"
pause
exit /b 1

:python_ok
echo [%date% %time%] PYTHON_CMD=!PYTHON_CMD! >> "%LOG%"

REM ============================================
REM 2/7. KIEM TRA NODE.JS VA BUILD FRONTEND
REM ============================================
if exist "web-ui\dist" goto :frontend_done

echo [2/7] Kiem tra Node.js...
echo [%date% %time%] Checking Node.js... >> "%LOG%"
node --version >nul 2>&1
if !errorLevel! == 0 (
    echo [2/7] Node.js... Hop le.
    echo [%date% %time%] Node.js found >> "%LOG%"
    goto :node_ok
)

echo [2/7] Khong tim thay Node.js. Dang tai ve tu dong...
echo [%date% %time%] Downloading Node.js LTS... >> "%LOG%"
curl -sL -o "%TEMP%\node-installer.msi" "https://nodejs.org/dist/v22.14.0/node-v22.14.0-x64.msi"
if not exist "%TEMP%\node-installer.msi" (
    echo LOI: Khong tai duoc Node.js! Kiem tra ket noi Internet.
    echo [%date% %time%] ERROR: Node.js download failed >> "%LOG%"
    pause
    exit /b 1
)

echo [2/7] Dang cai dat Node.js (silent)...
echo [%date% %time%] Installing Node.js silently... >> "%LOG%"
msiexec /i "%TEMP%\node-installer.msi" /qn /norestart
del "%TEMP%\node-installer.msi" >nul 2>&1

REM Cap nhat PATH cho session hien tai
set "PATH=%ProgramFiles%\nodejs;%PATH%"
node --version >nul 2>&1
if !errorLevel! neq 0 (
    echo LOI: Cai dat Node.js that bai!
    echo Vui long cai dat thu cong tu https://nodejs.org/
    echo [%date% %time%] ERROR: Node.js install failed >> "%LOG%"
    pause
    exit /b 1
)
echo [2/7] Cai dat Node.js... Hoan tat!
echo [%date% %time%] Node.js installed OK >> "%LOG%"

:node_ok
echo [2/7] Dang cai dat thu vien Frontend...
echo [%date% %time%] Running npm install in web-ui... >> "%LOG%"
pushd web-ui
call npm install
if !errorLevel! neq 0 (
    echo LOI: Khong cai dat duoc thu vien Frontend!
    echo [%date% %time%] ERROR: npm install failed >> "%LOG%"
    popd
    pause
    exit /b 1
)

echo [2/7] Dang build giao dien Web...
echo [%date% %time%] Running npm run build... >> "%LOG%"
call npm run build
if !errorLevel! neq 0 (
    echo LOI: Khong build duoc giao dien Web!
    echo [%date% %time%] ERROR: npm build failed >> "%LOG%"
    popd
    pause
    exit /b 1
)
popd
echo [2/7] Build Frontend... Hoan tat!
echo [%date% %time%] Frontend built OK >> "%LOG%"
goto :frontend_next

:frontend_done
echo [2/7] Frontend da build san... Bo qua.
echo [%date% %time%] Frontend dist already exists >> "%LOG%"

:frontend_next

REM ============================================
REM 3/7. TAI FFMPEG
REM ============================================
if exist "bin\ffmpeg\bin\ffmpeg.exe" goto :ffmpeg_done

echo [3/7] Dang tai FFmpeg khoang 80MB...
echo [%date% %time%] Downloading FFmpeg... >> "%LOG%"
mkdir bin >nul 2>&1
curl -sL -o bin\ffmpeg.zip https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip
if not exist "bin\ffmpeg.zip" (
    echo LOI: Khong tai duoc FFmpeg! Kiem tra ket noi Internet.
    echo [%date% %time%] ERROR: FFmpeg download failed >> "%LOG%"
    pause
    exit /b 1
)
echo Dang giai nen FFmpeg...
powershell -command "Expand-Archive -Path 'bin\ffmpeg.zip' -DestinationPath 'bin\temp_ffmpeg' -Force"
move bin\temp_ffmpeg\ffmpeg-master-latest-win64-gpl bin\ffmpeg >nul 2>&1
del bin\ffmpeg.zip
rmdir /S /Q bin\temp_ffmpeg
echo [3/7] FFmpeg... Hoan tat!
echo [%date% %time%] FFmpeg installed OK >> "%LOG%"
goto :ffmpeg_next

:ffmpeg_done
echo [3/7] FFmpeg da ton tai... Bo qua.
echo [%date% %time%] FFmpeg already exists >> "%LOG%"

:ffmpeg_next

REM ============================================
REM 3.5. TAI MediaMTX (WebRTC Live View)
REM ============================================
if exist "bin\mediamtx\mediamtx.exe" goto :mtx_done
echo [3.5/7] Dang tai MediaMTX khoang 30MB...
echo [%date% %time%] Downloading MediaMTX... >> "%LOG%"
powershell -command "Invoke-WebRequest -Uri 'https://github.com/bluenviron/mediamtx/releases/download/v1.17.1/mediamtx_v1.17.1_windows_amd64.zip' -OutFile 'bin\mediamtx.zip'"
if not exist "bin\mediamtx.zip" (
    echo CANH BAO: Khong tai duoc MediaMTX! Live view se dung MJPEG.
    echo [%date% %time%] WARN: MediaMTX download failed >> "%LOG%"
    goto :mtx_next
)
echo Dang giai nen MediaMTX...
powershell -command "Expand-Archive -Path 'bin\mediamtx.zip' -DestinationPath 'bin\mediamtx' -Force"
del bin\mediamtx.zip
echo [3.5/7] MediaMTX... Hoan tat!
echo [%date% %time%] MediaMTX installed OK >> "%LOG%"
goto :mtx_next

:mtx_done
echo [3.5/7] MediaMTX da ton tai... Bo qua.
echo [%date% %time%] MediaMTX already exists >> "%LOG%"

:mtx_next

REM ============================================
REM 4/7. TAO MOI TRUONG AO VA CAI THU VIEN
REM ============================================
echo [4/7] Khoi tao Moi Truong Ao va Cai dat Thu Vien...
if exist "venv" goto :venv_exists

echo [%date% %time%] Creating venv with !PYTHON_CMD!... >> "%LOG%"
!PYTHON_CMD! -m venv venv
if !errorLevel! neq 0 (
    echo LOI: Khong tao duoc moi truong ao venv!
    echo Thu xoa thu muc "venv" hien tai va chay lai.
    echo [%date% %time%] ERROR: venv creation failed >> "%LOG%"
    pause
    exit /b 1
)
echo [%date% %time%] venv created OK >> "%LOG%"

:venv_exists
echo [%date% %time%] Activating venv... >> "%LOG%"
call venv\Scripts\activate.bat
if !errorLevel! neq 0 (
    echo LOI: Khong kich hoat duoc venv!
    echo Thu xoa thu muc "venv" va chay lai script nay.
    echo [%date% %time%] ERROR: venv activation failed >> "%LOG%"
    pause
    exit /b 1
)

echo [%date% %time%] Upgrading pip... >> "%LOG%"
python -m pip install --upgrade pip
if !errorLevel! neq 0 (
    echo LOI: Khong nang cap duoc pip!
    echo [%date% %time%] ERROR: pip upgrade failed >> "%LOG%"
    pause
    exit /b 1
)

echo [%date% %time%] Installing requirements... >> "%LOG%"
python -m pip install -r requirements.txt
if !errorLevel! neq 0 (
    echo LOI: Khong cai dat duoc thu vien Python!
    echo Kiem tra ket noi Internet va thu lai.
    echo [%date% %time%] ERROR: pip install failed >> "%LOG%"
    pause
    exit /b 1
)
echo [%date% %time%] Requirements installed OK >> "%LOG%"

REM ============================================
REM 5/7. MO CONG TUONG LUA 8001
REM ============================================
echo [5/7] Mo cong Tuong Lua 8001...
netsh advfirewall firewall show rule name="V-Pack Monitor TCP 8001" >nul 2>&1
if !errorLevel! == 0 (
    echo Rule Tuong Lua dang ton tai. Bo qua...
) else (
    netsh advfirewall firewall add rule name="V-Pack Monitor TCP 8001" dir=in action=allow protocol=TCP localport=8001 >nul 2>&1
    echo Mo Port 8001... Hoan tat!
)
echo [%date% %time%] Firewall rule done >> "%LOG%"

REM ============================================
REM 6/7. TAO SHORTCUT
REM ============================================
echo [6/7] Tao loi tat ung dung o man hinh Desktop...
set "SHORTCUT_SCRIPT=%TEMP%\create_shortcut.vbs"
echo Set oWS = WScript.CreateObject("WScript.Shell") > "!SHORTCUT_SCRIPT!"
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\V-Pack Monitor.lnk" >> "!SHORTCUT_SCRIPT!"
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> "!SHORTCUT_SCRIPT!"
echo oLink.TargetPath = "%~dp0start_windows.bat" >> "!SHORTCUT_SCRIPT!"
echo oLink.WorkingDirectory = "%~dp0" >> "!SHORTCUT_SCRIPT!"
echo oLink.IconLocation = "%~dp0start_windows.bat, 0" >> "!SHORTCUT_SCRIPT!"
echo oLink.Save >> "!SHORTCUT_SCRIPT!"
cscript //nologo "!SHORTCUT_SCRIPT!"
del "!SHORTCUT_SCRIPT!"
echo [%date% %time%] Shortcut created >> "%LOG%"

echo.
echo ========================================================
echo [7/7] CAI DAT HOAN TAT THANG CONG!
echo 1. Da ban giao Phim Tat ra man hinh Desktop.
echo 2. Tu nay ve sau, chi can click dup vao [V-Pack Monitor] de mo Camera!
echo ========================================================
echo [%date% %time%] INSTALL COMPLETE >> "%LOG%"
pause
