# Plan 56: Session Lock via WebSocket

**Ngày**: 2026-04-24
**Mức độ**: Low — HTTP heartbeat đang work, WebSocket cho future real-time features
**Loại**: Architecture change (ROADMAP #3)

---

## Problem

Session lock hiện dùng HTTP polling:
- `POST /api/sessions/heartbeat` mỗi 30s từ frontend
- Session cleanup: timer-based, check on heartbeat miss

ROADMAP #3 muốn:
- WebSocket heartbeat (real-time hơn HTTP polling 30s)
- Chỉ 1 tab active per station — tab cũ bị kick + dialog
- Reconnect flow mượt

---

## Scope

### Phase 1: WebSocket Endpoint (Backend)

#### New endpoint:
```python
@router.websocket("/api/ws/session")
async def session_websocket(websocket: WebSocket, token: str = Query(...)):
    # Validate JWT token
    # Register connection per user+station
    # Send heartbeat request every 15s
    # On duplicate connection: kick old connection
```

#### Connection management:
- `_active_ws_sessions: dict[str, WebSocket]` — keyed by `user_id:station_id`
- On new connection for same user+station:
  1. Send `{"type": "kicked", "reason": "session_opened_elsewhere"}` to old connection
  2. Close old WebSocket
  3. Register new connection

### Phase 2: Frontend Migration

#### Replace HTTP heartbeat with WebSocket:
```javascript
// Replace: setInterval(() => fetch('/api/sessions/heartbeat'), 30000)
// With: WebSocket connection with auto-reconnect

useEffect(() => {
  const ws = new WebSocket(`ws://localhost:8001/api/ws/session?token=${token}`);
  ws.onmessage = (e) => {
    const msg = JSON.parse(e.data);
    if (msg.type === 'kicked') {
      showKickedDialog(msg.reason);
    }
    if (msg.type === 'heartbeat') {
      ws.send(JSON.stringify({ type: 'heartbeat_ack' }));
    }
  };
  // ... reconnect logic
}, [token, activeStationId]);
```

#### Kicked dialog:
- Modal: "Phiên làm việc đã được mở ở tab/device khác"
- Button: "Tiếp tục tại đây" (reconnects, kicks other tab)

### Phase 3: Keep HTTP heartbeat as fallback
- Don't remove HTTP heartbeat endpoint
- If WebSocket fails → fallback to HTTP polling
- Gradual migration, not big-bang

---

## Constraints

- WebSocket auth via query param token (WebSocket không support headers)
- Connection timeout: 60s không receive heartbeat_ack → close connection
- Keep HTTP heartbeat as fallback (backward compatible)
- `_active_ws_sessions` dict needs thread-safe access (asyncio.Lock)
- Clean up on: WebSocket close, user logout, server shutdown
- Max 1 WebSocket per user+station — enforce strictly
- Token refresh: khi JWT expire → client reconnect with new token

---

## Decision

**Khuyến nghị: KHÔNG LÀM NGAY.** HTTP heartbeat 30s đang hoạt động ổn. Chỉ migrate khi cần:
- Real-time single-tab enforcement (hiện tại operator có thể mở 2 tab)
- Kick notification phải tức thì (< 1s)
- Multi-device conflict management

Giữ plan này trong backlog.

---

## Verification

- [ ] WebSocket connects and authenticates
- [ ] Duplicate connection kicks old tab
- [ ] Kicked dialog shows in frontend
- [ ] "Tiếp tục tại đây" reconnects successfully
- [ ] HTTP heartbeat still works as fallback
- [ ] Session cleanup runs on WebSocket disconnect
- [ ] `pytest tests/ -q` pass
- [ ] `npm run build` pass
