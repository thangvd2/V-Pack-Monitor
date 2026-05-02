# V-Pack Monitor — Roadmap & Backlog (Updated 2026-05-02)

## COMPLETED
- [x] v3.5.0 — Infrastructure & Quality Overhaul (SSE auto-reconnect, Cloud Sync Scheduler, Camera Health Monitoring, Alembic migration, TypeScript, Pydantic, E2E Playwright)
- [x] v3.4.0 — Admin Tab Navigation & UI Revamp
- [x] v3.3.2 — Performance & Cleanup
- [x] v3.3.1 — Bugfixes & Cleanup
- [x] v3.3.0 — Phase 3 Infrastructure & Pydantic v2 Migration
- [x] v3.2.0 — .ai-sync Protocol, Release Workflow, Enforcement Layers
- [x] v3.1.0 — Auto-Stop Recording, Notification Sounds, Quality Enforcement
- [x] v3.0.0 — Major Security Hardening (111 issues: Fernet encryption, FK enforcement, thread locks, path traversal prevention, HTTP status codes, input validation, recorder path sanitization, AbortController, confirm modal)
- [x] v2.4.2 — Security & Stability Audit (22 issues fixed: FTS5 crash guard, Zip Slip prevention, SSE stale closure, CORS hardening, error boundary, search debounce)
- [x] v2.4.1 — Bugfix (semver version comparison for auto-update)
- [x] v2.4.0 — Video Search v2 (FTS5 full-text search, pagination, date range filter, status filter)
- [x] v2.3.2 — Unit Test Hardening Phase 1-6 (322 tests, coverage: database, auth, API, network, video worker, cloud sync, telegram)
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

### 1. ~~Unit Test Suite~~ ✅ DONE (322 tests)
- Phase 1+2: 84 tests (database.py + auth.py)
- Phase 3+4: 77 tests (API routes + helpers)
- Phase 5-10: 108 tests (security regression, network, video worker, API hardening, DB edge cases, cloud sync, telegram)
- Phase 11: 28 tests (video search FTS5 + pagination)
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

### 5. ~~Camera Health Monitoring~~ ✅ DONE (v3.5.0)
- ~~Auto-reconnect khi camera offline > X phút (configurable)~~
- ~~Telegram alert khi camera down lâu~~
- ~~Camera latency/quality metrics trong SystemHealth~~
- ~~Camera uptime percentage per day/week~~

### 6. ~~Video Search & Filter nâng cao~~ ✅ DONE (v2.4.0)
- FTS5 full-text search (replacing LIKE)
- Pagination (replacing LIMIT 100 cứng)
- Date range filter (from → to)
- Status filter (READY, RECORDING, PROCESSING, FAILED)
- Sort by recorded_at, waybill_code, station_name, status

### 7. UI/UX Polish
- [PLAN] Setup Modal upgrade — frontend validation + UX (#19)
- Dark/light theme toggle
- Notifications panel (camera down, storage full, new user login)
- Keyboard shortcuts reference panel
- Responsive table cho mobile (history cards)
- ~~`showAllRecords` chỉ limit trên mobile, full trên desktop~~ → replaced by server-side pagination (v2.4.0)

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
