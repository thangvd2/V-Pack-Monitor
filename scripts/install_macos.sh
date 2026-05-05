#!/bin/bash
cd "$(dirname "$0")/.."
# =============================================================================
# V-Pack Monitor - macOS Installer
# Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)
# =============================================================================

set -e

MTX_VERSION="1.17.1"
LOG="$(cd "$(dirname "$0")" && pwd)/install_log.txt"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"; }

echo "" > "$LOG"
log "Bat dau cai dat V-Pack Monitor"

echo ""
echo "========================================================"
echo "       CAI DAT V-PACK MONITOR CHO macOS"
echo "========================================================"
echo ""

# 1. Check Python 3.10+
echo "[1/6] Kiem tra Python..."
log "[1/6] Kiem tra Python..."
PYTHON=""
if command -v python3.14 &> /dev/null; then
    PYTHON=python3.14
elif command -v python3.13 &> /dev/null; then
    PYTHON=python3.13
elif command -v python3.12 &> /dev/null; then
    PYTHON=python3.12
elif command -v python3.11 &> /dev/null; then
    PYTHON=python3.11
elif command -v python3.10 &> /dev/null; then
    PYTHON=python3.10
elif command -v python3 &> /dev/null; then
    PYVER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    PYMAJOR=$(echo "$PYVER" | cut -d. -f1)
    PYMINOR=$(echo "$PYVER" | cut -d. -f2)
    if [ "$PYMAJOR" -ge 3 ] && [ "$PYMINOR" -ge 10 ]; then
        PYTHON=python3
    fi
fi

if [ -z "$PYTHON" ]; then
    echo "LOI: Khong tim thay Python 3.10+ tren may!"
    echo ""
    echo "Cai dat Python bang Homebrew:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
    echo "  brew install python@3.14"
    echo ""
    echo "Hoac tai truc tiep tu: https://www.python.org/downloads/"
    log "ERROR: Python not found"
    exit 1
fi

PYVER=$($PYTHON --version 2>&1)
echo "       $PYVER ... Hop le."
log "Python: $PYVER"

# 2. Check Node.js
echo "[2/6] Kiem tra Node.js..."
log "[2/6] Kiem tra Node.js..."
if command -v node &> /dev/null; then
    NODEVER=$(node --version)
    echo "       Node.js $NODEVER ... Hop le."
    log "Node.js: $NODEVER"
else
    echo "       Khong tim thay Node.js."
    echo "       Dang cai dat qua Homebrew..."
    if command -v brew &> /dev/null; then
        brew install node
        log "Node.js installed via Homebrew"
    else
        echo "LOI: Khong co Homebrew. Cai dat Node.js tu: https://nodejs.org/"
        log "ERROR: No Homebrew, cannot install Node.js"
        exit 1
    fi
fi

# 3. Check / Install FFmpeg
echo "[3/6] Kiem tra FFmpeg..."
log "[3/6] Kiem tra FFmpeg..."
if command -v ffmpeg &> /dev/null; then
    FFMPEG_VER=$(ffmpeg -version 2>&1 | head -1)
    echo "       $FFMPEG_VER ... Hop le."
    log "FFmpeg: $FFMPEG_VER"
else
    echo "       Khong tim thay FFmpeg."
    echo "       Dang cai dat qua Homebrew..."
    if command -v brew &> /dev/null; then
        brew install ffmpeg
        echo "       Da cai dat FFmpeg."
        log "FFmpeg installed via Homebrew"
    else
        echo "       Dang tai FFmpeg static build..."
        mkdir -p bin/ffmpeg/bin
        ARCH=$(uname -m)
        if [ "$ARCH" = "arm64" ]; then
            FFMPEG_ARCH="arm64"
        else
            FFMPEG_ARCH="amd64"
        fi
        FFMPEG_URL="https://github.com/abartyczek/ffmpeg-static-builder/releases/latest/download/ffmpeg-macos-${FFMPEG_ARCH}"
        curl -L -o bin/ffmpeg/bin/ffmpeg "$FFMPEG_URL"
        chmod +x bin/ffmpeg/bin/ffmpeg
        curl -L -o bin/ffmpeg/bin/ffprobe "${FFMPEG_URL/probe/probe}" 2>/dev/null || true
        chmod +x bin/ffmpeg/bin/ffprobe 2>/dev/null || true
        echo "       Da cai dat FFmpeg (static) vao bin/ffmpeg/."
        log "FFmpeg installed (static) to bin/ffmpeg/"
    fi
fi

# 4. Create venv + install Python deps
echo "[4/6] Khoi tao Moi Truong Ao va cai dat thu vien..."
log "[4/6] Creating venv + installing deps..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
log "Python deps installed OK"

# 5. Build frontend
echo "[5/6] Build giao dien Frontend..."
log "[5/6] Frontend..."
cd web-ui
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run build
cd ..
echo "       Build Frontend... Hoan tat!"
log "Frontend built OK"

# 6. Download MediaMTX for Live View
echo "[6/6] Cai dat MediaMTX (WebRTC Live View)..."
log "[6/6] MediaMTX..."
mkdir -p bin/mediamtx
if [ ! -f "bin/mediamtx/mediamtx" ]; then
    ARCH=$(uname -m)
    if [ "$ARCH" = "arm64" ]; then
        MTX_ARCH="darwin_arm64"
    else
        MTX_ARCH="darwin_amd64"
    fi
    MTX_URL="https://github.com/bluenviron/mediamtx/releases/download/v${MTX_VERSION}/mediamtx_v${MTX_VERSION}_${MTX_ARCH}.tar.gz"
    echo "       Dang tai MediaMTX v${MTX_VERSION} (${MTX_ARCH})..."
    curl -L -o /tmp/mediamtx.tar.gz "$MTX_URL"
    tar xzf /tmp/mediamtx.tar.gz -C bin/mediamtx mediamtx mediamtx.yml LICENSE
    rm -f /tmp/mediamtx.tar.gz
    chmod +x bin/mediamtx/mediamtx
    echo "       Da cai dat MediaMTX v${MTX_VERSION}."
    log "MediaMTX v${MTX_VERSION} installed"
else
    echo "       MediaMTX da duoc cai dat truoc do."
    log "MediaMTX already exists"
fi

echo ""
echo "========================================================"
echo " CAI DAT HOAN TAT!"
echo ""
echo " Chay lenh sau de khoi dong he thong:"
echo "   ./scripts/start.sh"
echo ""
echo " Hoac tao alias nhanh:"
echo "   chmod +x start.sh"
echo "   echo 'alias vpack=\"$(pwd)/start.sh\"' >> ~/.zshrc"
echo "========================================================"
log "INSTALL COMPLETE"
