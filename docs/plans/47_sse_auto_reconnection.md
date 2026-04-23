# Plan 47: SSE Auto-Reconnection

**Ngày**: 2026-04-24
**Mức độ**: High — Operator đang scan → network drop → UI stuck "packing", không auto-recover
**Loại**: Reliability improvement (frontend)

---

## Problem

Hiện EventSource (App.jsx:385) không có reconnection logic:
1. Network drop → EventSource tự retry nhưng **events bị mất** trong khoảng disconnect
2. Nếu EventSource fail hoàn toàn → UI không update nữa, operator không biết
3. UI có thể stuck ở "packing" status nếu mất event STOP/PROCESSING

---

## Scope

### Files to change:
- `web-ui/src/hooks/useSSE.js` (hoặc `App.jsx` nếu chưa extract hooks)

### Reconnection strategy:

| Event | Action |
|-------|--------|
| `EventSource.onerror` | Show toast "Mất kết nối. Đang thử lại..." |
| Auto-reconnect (built-in) | EventSource tự retry với increasing delay |
| `EventSource.OPEN` (reconnected) | Re-fetch all state: stations, records, status, storage |
| Max retries (10 failures) | Show MtxFallback-style warning "Không thể kết nối server" |
| Manual reconnect button | "Thử lại" button in connection status indicator |

### State sync on reconnect:
When SSE reconnects after disconnect, server state may have changed:
1. Re-fetch `GET /api/stations` — station list may have changed
2. Re-fetch `GET /api/records` — new records may exist
3. Re-fetch `GET /api/status` — packing status may have changed
4. Reset `packingStatus` based on actual server state (not stale SSE state)

### Connection status indicator:
- Small dot in header: 🟢 Connected / 🔴 Disconnected / 🟡 Reconnecting
- Click dot → manual reconnect attempt

---

## Constraints

- Không duplicate SSE connection (only 1 EventSource at a time)
- Reconnect attempts: exponential backoff 1s → 2s → 4s → ... → 30s cap
- Phải clean up EventSource properly on component unmount
- Connection status indicator không intrusive (small dot, not modal)
- Re-fetch on reconnect không spam server (batch requests)

---

## Verification

- [ ] `npm run build` pass
- [ ] `npm run lint` pass
- [ ] Simulate network disconnect → toast appears → auto-reconnect → state re-synced
- [ ] Simulate server restart → SSE reconnects after server up
- [ ] "packing" state recovers correctly after reconnect
- [ ] Connection status dot updates in real-time
