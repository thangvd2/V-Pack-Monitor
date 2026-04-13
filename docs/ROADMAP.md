# V-Pack Monitor — Roadmap & Backlog (Updated 2026-04-14)

## COMPLETED
- [x] v2.3.1 — Comprehensive Bug Fix (12 bugs: SQL injection, race condition, auth bypass, memory leaks)
- [x] v2.3.0 — Auto-Update System (1-click update, version badge, progress UI)
- [x] v2.2.4 — Security Hardening (26 vulnerabilities fixed)
- [x] v2.2.3 — Record Stream Toggle
- [x] v2.2.1 — Mobile Responsive Phase 1
- [x] v2.2.0 — Video Pipeline Reliability & UI Refactor
- [x] WebRTC Live View via MediaMTX
- [x] JWT Auth + RBAC
- [x] Dual Camera + PIP Mode
- [x] Dashboard & Analytics Pro
- [x] System Health Dashboard
- [x] User Management UI

---

## BACKLOG (Theo mức ưu tiên)

### 1. Unit Test Suite — Phase 3+4 (API Routes + Helpers)
- **DONE (Phase 1+2):** 84 tests, 94% coverage on `database.py` + `auth.py`
- Phase 3: API endpoint tests (login, stations, records, scan, sessions, SSE)
- Phase 4: Helper tests (RTSP URLs, conflict check)
- GitHub Actions CI: auto-run pytest on push

### 2. Smart Storage — 3-tier Video Management
- **Tier 1:** SSD (H:) — recent 7 ngày (fast random access)
- **Tier 2:** HDD (E:) — archive 1-6 tháng
- **Tier 3:** Compressed deep archive — H.264 CRF 28, tiết kiệm ~70% dung lượng
- Auto-migrate video cũ qua tier tiếp theo
- Configurable retention per tier
- Storage dashboard — dung lượng từng tier, số file, auto-cleanup status

### 3. Session Lock (1 browser tab/station)
- WebSocket heartbeat thay HTTP polling 30s (real-time hơn)
- Chỉ 1 tab active per station, tab cũ bị kick + dialog cảnh báo
- Reconnect flow mượt khi tab bị kick

### 4. ~~Auto-Update System~~ ✅ DONE (v2.3.0)
- Check GitHub release mới khi startup
- 1-click update (download zip + extract + restart)
- Version badge trên UI header
- Changelog popup sau khi update

### 5. Camera Health Monitoring
- Auto-reconnect khi camera offline > X phút (configurable)
- Telegram alert khi camera down lâu
- Camera latency/quality metrics trong SystemHealth
- Camera uptime percentage per day/week

### 6. Video Search & Filter nâng cao
- Filter theo date range (from → to), station, status
- Pagination (hiện LIMIT 100 cứng)
- Batch export CSV nhiều ngày
- Full-text search waybill code (SQLite FTS5)
- Sort by date, station, status

### 7. UI/UX Polish
- [PLAN] Setup Modal upgrade — frontend validation + UX (#19)
- Dark/light theme toggle
- Notifications panel (camera down, storage full, new user login)
- Keyboard shortcuts reference panel
- Responsive table cho mobile (history cards)
- `showAllRecords` chỉ limit trên mobile, full trên desktop

### 8. Infrastructure
- Docker Compose production config (MediaMTX + V-Pack + SQLite volume)
- GitHub Actions CI/CD (lint, build, auto-tag release)
- Backup/restore SQLite DB
- Log rotation cho server logs
- Graceful shutdown handling (SIGTERM/SIGINT)

### 9. Future Features
- Multi-warehouse support (nhiều kho, mỗi kho nhiều trạm)
- API key cho tích hợp bên ngoài (WMS/ERP)
- Video annotation — ghi chú trên timeline (VD: "đóng sai kiện này")
- AI integration — detect missing items, wrong packaging
- Mobile app (React Native hoặc PWA)
