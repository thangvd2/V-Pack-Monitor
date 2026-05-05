#!/bin/bash
cd "$(dirname "$0")/.."
echo "====================================="
echo " KHOY DONG V-PACK MONITOR SERIES"
echo "====================================="
echo "Dang bat may chu Backend va Web..."

ulimit -n 4096 2>/dev/null
mkdir -p recordings

# === Check if frontend needs rebuild ===
if [ ! -f "web-ui/dist/index.html" ]; then
    echo "[Frontend] Dang build giao dien Web lan dau..."
    (cd web-ui && npm install && npm run build)
    if [ $? -ne 0 ]; then
        echo "LOI: Build frontend that bai!"
        exit 1
    fi
    echo "[Frontend] Build hoan tat!"
fi

MTX_PID=""

if [ -f "bin/mediamtx/mediamtx" ]; then
    echo "Dang khoi dong MediaMTX (WebRTC Live View)..."
    chmod +x bin/mediamtx/mediamtx
    bin/mediamtx/mediamtx bin/mediamtx/mediamtx.yml &
    MTX_PID=$!
    sleep 2
fi

if [ -d "bin/ffmpeg/bin" ]; then
    export PATH="$(pwd)/bin/ffmpeg/bin:$PATH"
fi

if [ ! -f "venv/bin/activate" ]; then
    echo ""
    echo "LOI: Khong tim thay moi truong ao venv!"
    echo "Vui long chay install_macos.sh truoc."
    echo ""
    exit 1
fi

source venv/bin/activate
python3 -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001 &
SERVER_PID=$!

cleanup() {
    echo ""
    echo "Dang tat server..."
    kill $MTX_PID 2>/dev/null
    kill $SERVER_PID 2>/dev/null
    wait $MTX_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    echo "Da tat."
    exit 0
}
trap cleanup SIGINT SIGTERM

sleep 3

if which open > /dev/null
then
    open "http://localhost:8001"
elif which xdg-open > /dev/null
then
    xdg-open "http://localhost:8001"
fi

echo "Da mo trinh duyet!"
echo "An Ctrl+C de tat server."
wait $SERVER_PID
