# Plan 48: WebSocket Migration (SSE → WebSocket)

**Ngày**: 2026-04-24
**Mức độ**: Low — SSE đang hoạt động tốt, WebSocket cho future 2-way communication
**Loại**: Architecture change

---

## Problem

SSE là 1 chiều (server → client). Các limitation:
- Admin không thể push command đến operator qua SSE
- Không có real-time collaboration (2 operators cùng trạm)
- Polling vẫn cần cho một số operations (health, analytics)

WebSocket cho phép 2 chiều, nhưng:
- SSE đang hoạt động ổn định
- Thêm complexity (connection management, reconnection, message ordering)
- MediaMTX đã dùng WebRTC, không liên quan

---

## Scope

### Phase 1: WebSocket Server (backend)
- Add `websockets` hoặc dùng FastAPI WebSocket
- New endpoint `WS /api/ws` — authenticate via query param token
- Message format: `{"type": "video_status", "data": {...}}`
- Keep SSE endpoint working (backward compatible)

### Phase 2: WebSocket Client (frontend)
- Replace `EventSource` with WebSocket client
- Auto-reconnect với exponential backoff
- Heartbeat ping/pong every 30s

### Phase 3: New capabilities (future)
- Admin → Operator: push notification, force stop recording
- Multi-operator: see who's scanning which station
- Real-time collaboration features

---

## Constraints

- **Phải backward compatible** — SSE endpoint vẫn hoạt động trong quá trình migration
- WebSocket không thay thế polling cho health/analytics (vẫn dùng REST)
- Thêm dependency: `websockets` (nếu không dùng FastAPI WebSocket)
- Migration từng bước: WebSocket cho events mới, SSE cho events cũ

---

## Decision

**Khuyến nghị: KHÔNG LÀM NGAY.** SSE đang work. Chỉ migrate khi cần:
- Admin push commands to operator
- Multi-operator collaboration
- Real-time bidirectional features

Giữ plan này trong backlog.

---

## Verification

- [ ] WebSocket server handles 50 concurrent connections
- [ ] Auto-reconnect within 5s of disconnect
- [ ] All SSE events delivered via WebSocket
- [ ] SSE endpoint still works (backward compat)
- [ ] `pytest tests/ -q` pass
- [ ] `npm run build` pass
