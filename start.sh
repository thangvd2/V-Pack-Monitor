#!/bin/bash
echo "====================================="
echo " KHOY DONG V-PACK MONITOR SERIES"
echo "====================================="
echo "Dang bat may chu Backend va Web..."

# Create recordings dir if missing
mkdir -p recordings

# Start server
python3 -m uvicorn api:app --host 0.0.0.0 --port 8001 &
SERVER_PID=$!

sleep 2

# Open browser
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
