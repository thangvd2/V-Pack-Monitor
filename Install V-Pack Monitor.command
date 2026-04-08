#!/bin/bash
# =============================================================================
# V-Pack Monitor - macOS Installer
# =============================================================================

cd "$(dirname "$0")"

set -e

echo ""
echo "========================================================"
echo "       CAI DAT V-PACK MONITOR CHO macOS"
echo "========================================================"
echo ""

# 1. Check Python 3.10+
echo "[1/4] Kiem tra Python..."
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
    exit 1
fi

PYVER=$($PYTHON --version 2>&1)
echo "       $PYVER ... Hop le."

# 2. Check Node.js
echo "[2/4] Kiem tra Node.js..."
if command -v node &> /dev/null; then
    NODEVER=$(node --version)
    echo "       Node.js $NODEVER ... Hop le."
else
    echo "       Khong tim thay Node.js."
    echo "       Dang cai dat qua Homebrew..."
    if command -v brew &> /dev/null; then
        brew install node
    else
        echo "LOI: Khong co Homebrew. Cai dat Node.js tu: https://nodejs.org/"
        exit 1
    fi
fi

# 3. Create venv + install Python deps
echo "[3/4] Khoi tao Moi Truong Ao va cai dat thu vien..."
if [ ! -d "venv" ]; then
    $PYTHON -m venv venv
fi
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 4. Build frontend
echo "[4/4] Build giao dien Frontend..."
cd web-ui
if [ ! -d "node_modules" ]; then
    npm install
fi
npm run build
cd ..

echo ""
echo "========================================================"
echo " CAI DAT HOAN TAT!"
echo ""
echo " Chay lenh sau de khoi dong he thong:"
echo "   ./start.sh"
echo ""
echo " Hoac tao alias nhanh:"
echo "   chmod +x start.sh"
echo "   echo 'alias vpack=\"$(pwd)/start.sh\"' >> ~/.zshrc"
echo "========================================================"
