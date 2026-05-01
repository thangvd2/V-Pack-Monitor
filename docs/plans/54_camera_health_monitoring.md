# Plan 54: Camera Health Monitoring

**Ngày**: 2026-04-24
**Mức độ**: Medium — Camera down không có alert, operator không biết
**Loại**: New feature (ROADMAP #5)

---

**Status**: Done — PR #81 merged to dev

## Problem

Khi camera offline (đổi IP, mất mạng, restart):
- Operator không biết camera đã down → scan START → FFmpeg fail → mất video
- Admin không nhận alert → phát hiện muộn
- Không có camera uptime/latency metrics
- Camera auto-discovery chỉ chạy khi scan START (reactive), không proactive

---

## Scope

### Phase 1: Camera Reachability Check (Background)

#### Backend:
- `api.py` — Add `_periodic_camera_health_check()` async task (every 60s)
- For each station with IP configured:
  - Ping camera IP (subprocess `ping -c 1 -W 2`)
  - Track: `last_seen` timestamp, `is_online` status
  - Store in-memory dict: `_camera_health = {station_id: {online, last_seen, latency_ms}}`
- On status change (online→offline or offline→online):
  - Log event to audit_log
  - Send Telegram notification (if configured)
  - Update SSE state (new event type: `camera_status`)

#### New API endpoints:
```
GET /api/camera-health → {_camera_health dict}
```

### Phase 2: Camera Down Alert

#### Telegram alert:
- Camera offline > X phút (configurable, default 5 min):
  ```
  ⚠️ Camera DOWN
  Trạm: {station_name}
  IP: {ip_camera}
  Thời gian mất kết nối: {timestamp}
  ```
- Camera back online:
  ```
  ✅ Camera UP
  Trạm: {station_name}
  Thời gian gián đoạn: {duration}
  ```

### Phase 3: Frontend Integration

#### SystemHealth.jsx:
- Add "Camera Health" section
- Per-station status: 🟢 Online / 🔴 Offline (X phút)
- Last seen timestamp
- Latency (ms)

#### App.jsx:
- Camera offline indicator in station card/list
- Red dot overlay on offline station

### Settings:
- `CAMERA_HEALTH_CHECK_INTERVAL` (seconds, default 60)
- `CAMERA_DOWN_ALERT_MINUTES` (default 5)

---

## Constraints

- Ping check chạy trong thread pool (không block event loop)
- Max 10 stations × 1 ping mỗi 60s = minimal load
- Camera health dict in-memory only (không persist — rebuild on restart)
- Telegram alert: max 1 alert per camera per 30 min (avoid spam)
- SSE event `camera_status`: chỉ fire khi status THAY ĐỔI (không spam mỗi 60s)
- Phải handle: station thêm/xóa → health dict update
- Ping timeout: 2 seconds max per camera

---

## Verification

- [ ] Camera goes offline → detected within 60s
- [ ] Camera offline > 5 min → Telegram alert sent
- [ ] Camera comes back → "UP" notification sent
- [ ] SystemHealth shows camera status per station
- [ ] Adding/removing station updates health check list
- [ ] No alert spam (max 1 per 30 min per camera)
- [ ] `pytest tests/ -q` pass
