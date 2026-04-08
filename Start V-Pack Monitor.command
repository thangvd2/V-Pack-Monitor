#!/bin/bash
cd "$(dirname "$0")"

echo "====================================="
echo " KHOY DONG V-PACK MONITOR SERIES"
echo "====================================="
echo "Dang bat may chu Backend va Web..."

mkdir -p recordings

source venv/bin/activate
python3 -m uvicorn api:app --host 0.0.0.0 --port 8001 &
SERVER_PID=$!

cleanup() {
    echo ""
    echo "Dang tat server..."
    kill -9 $SERVER_PID 2>/dev/null
    wait $SERVER_PID 2>/dev/null
    echo "Da tat."
    exit 0
}
trap cleanup SIGINT SIGTERM

sleep 2

if which xdg-open > /dev/null
then
  xdg-open "http://localhost:8001"
elif which open > /dev/null
then
  open "http://localhost:8001"
fi

echo "Da mo trinh duyet!"
echo "An Ctrl+C de tat server."
wait $SERVER_PID
