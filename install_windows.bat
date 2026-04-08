@echo off
setlocal EnableDelayedExpansion

REM ===== V-PACK MONITOR WINDOWS INSTALLER =====
REM Chạy với Quyền Administrator để cấp phép Tường Lửa
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Kich hoat Quyen Administrator... Thanh Cong.
) else (
    echo [CANH BAO] Ban chua chay voi Quyen Administrator! 
    echo Mot so tinh nang ghep noi mang LAN co the se khong hoat dong.
    echo Vui long tat bang nay, Nhan chuot phai vao file install_windows.bat va chon "Run as administrator".
    pause
    exit /b 1
)

echo.
echo ========================================================
echo        CAI DAT V-PACK MONITOR CHO KHO XUONG
echo ========================================================
echo.

REM 1. KIEM TRA PYTHON
python --version >nul 2>&1
if %errorLevel% == 0 (
    echo [1/5] Kiem tra Python... Hop le.
) else (
    py --version >nul 2>&1
    if %errorLevel% == 0 (
        echo [1/5] Phat hien Python qua lenh "py". Dang tao alias...
        doskey python=py $*
        set PYTHON_CMD=py
    ) else (
        echo [1/5] LOI: Khong tim thay Python tren may!
        echo.
        echo Vui long cai dat Python 3 tu:
        echo   - https://www.python.org/downloads/
        echo   - Hoac mo Microsoft Store tim "Python"
        echo.
        echo LUU Y: Khi cai dat, nho check "Add Python to PATH" o dau tien!
        echo.
        pause
        exit /b 1
    )
)

REM 2. TAI FFMPEG VA GIAI NEN NEN TRONG THU MUC BIN (LOCAL)
if not exist "bin\ffmpeg\bin\ffmpeg.exe" (
    echo [2/5] Chua co FFmpeg tren he thong, dang tai ve tu dong (Bang thong ~ 80MB)...
    mkdir bin >nul 2>&1
    curl -sL -o bin\ffmpeg.zip https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip
    
    echo Dang giai nen FFmpeg... (Chung ta da co the uong 1 ngum nuoc)
    powershell -command "Expand-Archive -Path 'bin\ffmpeg.zip' -DestinationPath 'bin\temp_ffmpeg' -Force"
    
    echo Sap xep lai thu muc truc quan hon...
    move bin\temp_ffmpeg\ffmpeg-master-latest-win64-gpl bin\ffmpeg >nul 2>&1
    del bin\ffmpeg.zip
    rmdir /S /Q bin\temp_ffmpeg
    echo Tai FFmpeg... Hoan tat!
) else (
    echo [2/5] FFmpeg da ton tai trong thu muc \bin... Bo qua.
)

REM 3. TAO MOI TRUONG AO VA CAI THU VIEN
echo [3/5] Khoi tao Moi Truong Ao (Virtual Environment) va Cai dat Thu Vien...
if not exist "venv" (
    if defined PYTHON_CMD (
        %PYTHON_CMD% -m venv venv
    ) else (
        python -m venv venv
    )
    if %errorLevel% neq 0 (
        echo.
        echo LOI: Khong tao duoc moi truong ao venv!
        echo Thu xoa thu muc "venv" hien tai va chay lai.
        echo.
        pause
        exit /b 1
    )
)
call venv\Scripts\activate.bat
if %errorLevel% neq 0 (
    echo.
    echo LOI: Khong kich hoat duoc venv!
    echo Thu xoa thu muc "venv" va chay lai script nay.
    echo.
    pause
    exit /b 1
)
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorLevel% neq 0 (
    echo.
    echo LOI: Khong cai dat duoc thu vien Python!
    echo Kiem tra ket noi Internet va thu lai.
    echo.
    pause
    exit /b 1
)

REM 4. MO CONG TUONG LUA 8001
echo [4/5] Cho phep cac thiet bi cung mang LAN truy cap den Server (Mo Tuong Lua qua Port 8001)...
netsh advfirewall firewall show rule name="V-Pack Monitor TCP 8001" >nul 2>&1
if %errorLevel% == 0 (
    echo Rule Tuong Lua dang ton tai. Bo qua...
) else (
    netsh advfirewall firewall add rule name="V-Pack Monitor TCP 8001" dir=in action=allow protocol=TCP localport=8001 >nul 2>&1
    echo Mo Port 8001... Hoan tat!
)

REM 5. TAO SHORTCUT CHUAN MAU CHUYEN NGHIEP
echo [5/5] Tao loi tat ung dung o man hinh Desktop...
set SHORTCUT_SCRIPT=%TEMP%\create_shortcut.vbs
echo Set oWS = WScript.CreateObject("WScript.Shell") > %SHORTCUT_SCRIPT%
echo sLinkFile = oWS.SpecialFolders("Desktop") ^& "\V-Pack Monitor.lnk" >> %SHORTCUT_SCRIPT%
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> %SHORTCUT_SCRIPT%
echo oLink.TargetPath = "%~dp0start_windows.bat" >> %SHORTCUT_SCRIPT%
echo oLink.WorkingDirectory = "%~dp0" >> %SHORTCUT_SCRIPT%
echo oLink.IconLocation = "%~dp0start_windows.bat, 0" >> %SHORTCUT_SCRIPT%
echo oLink.Save >> %SHORTCUT_SCRIPT%
cscript //nologo %SHORTCUT_SCRIPT%
del %SHORTCUT_SCRIPT%

echo.
echo ========================================================
echo CAI DAT HOAN TAT THANG CONG!
echo 1. Da ban giao Phim Tat ra man hinh Desktop.
echo 2. Tu nay ve sau, chi can click dup vao [V-Pack Monitor] de mo Camera!
echo ========================================================
pause
