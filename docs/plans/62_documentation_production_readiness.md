# Plan 62: Documentation Production Readiness & Code Hardening

> **Status:** DONE
> **Priority:** HIGH — Blocker for sales
> **Scope:** 3 critical doc rewrites + README fixes + code cleanup + version bumps + archive
> **Estimated Effort:** 3-4 hours

---

## Background

Full documentation audit revealed 3 customer-facing docs stuck at v2.1.0 (missing 7 releases of features), broken placeholder image in README, hardcoded dev-only CORS origins in production code, and several docs with stale version headers. System is v3.5.0 but documentation says v2.1.0 — this blocks sales readiness.

---

## Phase 1: Critical Doc Rewrites (BLOCKING)

### Task 1.1: Update `docs/USER_GUIDE_ADMIN.md` (v2.1.0 → v3.5.0)

**File:** `docs/USER_GUIDE_ADMIN.md` (534 lines)

**Changes REQUIRED:**

1. **Line 3**: Title version `v2.1.0` → `v3.5.0`
2. **Section 3.1 (Thanh Header)**: Major rewrite needed.
   - v3.4.0 introduced **Admin Tab Navigation** with 2 tabs: `📹 Vận hành` (Live Cameras + History) and `📊 Tổng quan` (Dashboard Stats + SystemHealth)
   - Settings icon location changed — now in each station's detail view (drill-down), not directly in header
   - Users icon moved — accessible from Admin tab navigation
   - Activity icon now part of `📊 Tổng quan` tab, not standalone header button
   - Add description of tab navigation UI
3. **Section 3.3 (Vùng Nội Dung Chính)**: Add 5th mode — Admin Tab Navigation view
   - `📹 Vận hành` tab: Grid of all camera cards with live view + recording status
   - `📊 Tổng quan` tab: Dashboard stats + SystemHealth combined
   - Drill-down: Click camera card → single station detail view
4. **Section 4.1 (Cấu Hình Trạm)**: Add stream quality toggle
   - **Chất lượng ghi:** 1080p (main stream) / 480p (sub stream) — saves storage
   - Note: Only available in SINGLE mode
5. **Section 5.1 (Camera Live View)**: Add auto-stop timer
   - Recording auto-stops at **10 minutes** if no new barcode scanned
   - **Warning beep** at 9 minutes
   - Badge shows countdown timer near auto-stop threshold
6. **New section or subsection**: Camera Health Monitoring (v3.5.0)
   - Periodic health check every 60 seconds
   - Status indicators: 🟢 Online, 🔴 Offline (red pulse on dashboard)
   - Latency display in SystemHealth
   - Telegram alert when camera offline > 5 minutes
7. **Section 8 (Dashboard)**: Add Cloud Sync Scheduler info
   - Scheduled backup (default 02:00 daily)
   - Toggle on/off + time picker in SetupModal → Hệ thống chung
8. **Section 9 (Sức Khỏe Hệ Thống)**: Update with camera health section
   - Camera Health table with online/offline status + latency
   - Red pulse indicator explanation
   - Telegram alert configuration reference
9. **Section 11 (Đồng Bộ Cloud)**: Add Cloud Sync Scheduler
   - Scheduled backup feature
   - Configuration in SetupModal → Hệ thống chung → Cloud Sync Schedule
   - Toggle on/off, set time
10. **Section 13 (Khắc Phục Sự Cố)**: Add new troubleshooting entries:
    - Camera offline / red pulse indicator
    - Auto-stop timer triggered unexpectedly
    - SSE reconnection (auto-recovers, no action needed)
    - Cloud sync schedule not running
    - Video processing stuck at "Đang xử lý"

**MUST DO:**
- Keep ALL existing content that's still accurate — only update/add what changed
- Maintain same Vietnamese language and tone
- Keep same markdown section numbering style
- Test all internal anchor links after restructuring
- Regenerate PDF after update

**MUST NOT DO:**
- Do NOT change the overall structure/flow unless necessary for new features
- Do NOT remove existing troubleshooting entries — only ADD new ones
- Do NOT change Vietnamese terminology (e.g., keep "Trạm", "Ghi hình", not "Station", "Recording")

---

### Task 1.2: Update `docs/USER_GUIDE_OPERATOR.md` (v2.1.0 → v3.5.0)

**File:** `docs/USER_GUIDE_OPERATOR.md` (272 lines)

**Changes REQUIRED:**

1. **Line 3**: Title version `v2.1.0` → `v3.5.0`
2. **Section 5.2 (Dừng Ghi Hình)**: Add auto-stop timer
   - Add 4th way to stop: **Tự động dừng sau 10 phút** nếu không quét mã mới
   - Warning beep at 9 minutes to alert operator
   - Video is saved automatically when auto-stop triggers
3. **Section 4.1 (Thanh Header)**: Minor update
   - Note that header layout may differ slightly depending on version
   - Camera health indicator may appear (red pulse when camera offline)
4. **Add new subsection after 5.2**: **Âm thanh cảnh báo**
   - Beep khi scan thành công mã vận đơn
   - Warning beep ở phút thứ 9 (sắp auto-stop)
   - Error sound khi quét mã thất bại
   - Sound khi dừng ghi thành công
5. **Section 13 (Khắc Phục Sự Cố)**: Add new entries:
   - "Camera nhấp nháy đỏ" → Camera offline, báo Administrator
   - "Tự dừng ghi hình sau 10 phút" → Bình thường, đây là tính năng tự động. Quét mã mới để tiếp tục.
   - "Mất kết nối rồi tự khôi phục" → SSE auto-reconnection, không cần làm gì
6. **Line 42**: Session timeout — verify it's still 8 hours (check api.py/auth.py)

**MUST DO:**
- Keep operator-friendly tone (simple, direct language)
- All new features must be explained in everyday terms
- Regenerate PDF after update

**MUST NOT DO:**
- Do NOT add admin-only features (cloud sync scheduler, user management, etc.)
- Do NOT change existing accurate content

---

### Task 1.3: Update `README_SETUP.md` (v2.1.0 → v3.5.0)

**File:** `README_SETUP.md` (98 lines)

**Changes REQUIRED:**

1. **Line 1**: Title version `v2.1.0` → `v3.5.0`
2. **Section "Tiền Đề Cần Chuẩn Bị"**: Add hardware requirements link
   - Add: "Xem chi tiết cấu hình tối thiểu/khuyến nghị tại: [HARDWARE_REQUIREMENTS.md](docs/HARDWARE_REQUIREMENTS.md)"
3. **Section Bước 3**: Minor update
   - Note about stream quality toggle (1080p/480p) when creating station
4. **Section Bước 4 (Thiết Lập Quản Trị)**:
   - Update UI references: v3.4.0 changed to tab navigation
   - **Cloud Sync Scheduler**: Mention scheduled backup option (default 02:00)
   - **Camera Health Monitoring**: Mention auto-check + Telegram alert
   - Reference: Settings accessible via camera card drill-down in Admin grid
5. **Section Bước 5 (Bàn Giao cho Khách)**:
   - Add: Auto-stop timer (10 min) — camera tự dừng sau 10 phút nếu quên quét mã mới
   - Add: Warning sounds — beep cảnh báo
   - Add: EXIT code behavior — quét mã EXIT để dừng không lưu (dùng khi đóng sai)
   - Update: "nhấn foot switch" → verify if foot switch is still supported or remove
6. **Add new section**: **Tính Năng Tự Động (v3.5.0)**
   - Auto-stop timer: 10 phút không scan → tự dừng
   - Camera health: Tự kiểm tra 60s, cảnh báo Telegram khi offline > 5 phút
   - SSE auto-reconnect: Tự khôi phục kết nối khi mất mạng
   - Cloud sync scheduler: Backup tự động theo lịch (mặc định 02:00)

**MUST DO:**
- Keep sales-friendly tone (brief, punchy, action-oriented)
- All instructions must be field-ready for deployment technicians
- Regenerate PDF if one exists

**MUST NOT DO:**
- Do NOT make it too long — this is a quick-reference guide for field deployment
- Do NOT add developer-facing information

---

## Phase 2: README.md Fixes

### Task 2.1: Fix README.md issues

**File:** `README.md`

**Changes REQUIRED:**

1. **Line 5**: Remove broken placeholder image reference
   - Option A: Remove the line entirely
   - Option B (preferred): Replace with a simple text-based architecture diagram using ASCII art or mermaid (compatible with GitHub)
   ```markdown
   ## 🏗 Kiến Trúc Hệ Thống (v3.5.0)

   ```
   Camera IP (RTSP) ──┬── Main Stream (HEVC) ──→ FFmpeg ──→ MPEG-TS ──→ MP4 (recording)
                      └── Sub Stream (H.264) ──→ MediaMTX ──→ WebRTC ──→ Browser (live view)
                                                                   ↕
   Scanner USB ──→ Browser ──→ FastAPI ──→ SQLite DB ──→ Cloud Sync (Google Drive / S3)
   ```
   ```
2. **Architecture section header**: `v3.2.0` → `v3.5.0`
3. **macOS tip** (around line 85): Fix `install.sh` → `install_macos.sh`
4. **Troubleshooting section**: Expand from 2 to 8+ Q&A items:
   - Keep existing 2 items
   - Add: Camera offline / red pulse indicator
   - Add: MediaMTX not running
   - Add: Auto-stop timer behavior
   - Add: Browser compatibility (Chrome/Edge recommended, not Safari)
   - Add: Port requirements (554 RTSP, 8889 WebRTC, 8001 API)
   - Add: FFmpeg not found
   - Add: Database locked error

**MUST DO:**
- Keep README as the "first impression" document
- ASCII diagram must render correctly on GitHub

**MUST NOT DO:**
- Do NOT add too much detail — README should be concise, link to docs/ for details

---

## Phase 3: Code Fixes

### Task 3.1: Remove dev-only CORS origins from `api.py`

**File:** `api.py` lines 777-783

**Change:**
```python
# BEFORE:
origins = [
    "http://localhost:8001",
    "http://127.0.0.1:8001",
    "http://localhost:3000",      # REMOVE - dev only
    "http://127.0.0.1:3000",     # REMOVE - dev only
    "http://localhost:5173",      # REMOVE - dev only
    "http://127.0.0.1:5173",     # REMOVE - dev only
]

# AFTER:
origins = [
    "http://localhost:8001",
    "http://127.0.0.1:8001",
]
```

### Task 3.2: Move `test_rtsp.py` to `scripts/`

**Action:**
1. Move `test_rtsp.py` → `scripts/test_rtsp.py`
2. Verify no other code references this file

### Task 3.3: Create `.env.example`

**New file:** `.env.example`

```env
# V-Pack Monitor — Environment Variables
# Copy this file to .env and customize as needed

# Server
VPACK_HOST=0.0.0.0          # Bind host (default: 0.0.0.0)
# VPACK_PORT=8001            # Bind port (default: 8001) — NOT YET SUPPORTED

# Security
# VPACK_SECRET=             # JWT + encryption key (auto-generated if not set)

# MediaMTX
MTX_API=http://127.0.0.1:9997   # MediaMTX API endpoint
MTX_HOST=127.0.0.1              # MediaMTX WebRTC host (for iframe URLs)
```

**MUST DO:**
- Keep it minimal — only document variables that are actually read by the code
- Verify each env var exists in the codebase with `os.environ.get()`

**MUST NOT DO:**
- Do NOT include actual secrets or default passwords
- Do NOT add env vars that don't exist in the code yet

---

## Phase 4: Version Bumps & Doc Updates

### Task 4.1: Update `docs/ROADMAP.md`

**Changes:**
1. Header: `(Updated 2026-04-15)` → `(Updated 2026-05-02)`
2. Add to COMPLETED list:
   - `v3.5.0 — Infrastructure & Quality Overhaul (SSE auto-reconnect, Cloud Sync Scheduler, Camera Health Monitoring, Alembic migration, TypeScript, Pydantic, E2E Playwright)`
   - `v3.4.0 — Admin Tab Navigation & UI Revamp`
   - `v3.3.2 — Performance & Cleanup`
   - `v3.3.1 — Bugfixes & Cleanup`
3. Section 5 (Camera Health Monitoring): Mark as ~~DONE~~ ✅ DONE (v3.5.0)
4. Section 8 (Infrastructure): Mark partial items as done:
   - ~~GitHub Actions CI/CD~~ ✅ DONE (v3.0.0)
   - ~~Docker Compose production~~ → Still backlog (Plan 50)
5. Section 7 (UI/UX Polish): Update status of items

### Task 4.2: Bump version in `docs/DESIGN_PATTERNS.md`

**Changes:**
1. Line 1: `v3.4.0` → `v3.5.0`
2. Update audit date
3. Review "Opportunities" section — mark completed items:
   - Custom hooks extraction → DONE (v3.5.0)
   - Parameterized tests → DONE (v3.5.0)
   - Error boundaries → DONE (v3.5.0)

### Task 4.3: Bump version in `docs/BEST_PRACTICES.md`

**Changes:**
1. Line 1: `v3.4.0` → `v3.5.0`
2. Verify JWT token duration (15min access + 7day refresh vs 8-hour tokens) — check `auth.py`
3. Update test count if needed (326 tests)

### Task 4.4: Update `docs/QUALITY_CONTROL.md`

**Changes:**
1. Update tooling status table to v3.5.0
2. Mark "Pre-commit hooks" as DONE (v3.1.0)
3. Mark "E2E tests" as DONE (v3.5.0 Playwright)
4. Update test count to 326

---

## Phase 5: Archive Outdated Docs

### Task 5.1: Archive `docs/windows_fixes_needed.md`

**Action:**
1. Create `docs/archive/` directory
2. Move `docs/windows_fixes_needed.md` → `docs/archive/windows_fixes_needed.md`
3. Add note at top: "⚠️ OUTDATED — All issues fixed in v2.2.2 and v3.0.0. Kept for historical reference."

### Task 5.2: Archive `docs/brainstorm_roadmap.md`

**Action:**
1. Move `docs/brainstorm_roadmap.md` → `docs/archive/brainstorm_roadmap.md`
2. Add note at top: "⚠️ OUTDATED — Post-v2.1.0 brainstorm. Most items implemented in v2.2-v3.5. Kept for historical reference."

---

## Execution Order

```
Phase 3 (Code fixes) — Quick, independent, no doc dependency
  ├── 3.1 CORS cleanup (5 min)
  ├── 3.2 Move test_rtsp.py (2 min)
  └── 3.3 Create .env.example (5 min)

Phase 2 (README fixes) — Independent
  └── 2.1 Fix README.md (15 min)

Phase 4 (Version bumps) — Independent
  ├── 4.1 ROADMAP.md (10 min)
  ├── 4.2 DESIGN_PATTERNS.md (5 min)
  ├── 4.3 BEST_PRACTICES.md (5 min)
  └── 4.4 QUALITY_CONTROL.md (5 min)

Phase 5 (Archive) — Independent
  ├── 5.1 Archive windows_fixes_needed.md (2 min)
  └── 5.2 Archive brainstorm_roadmap.md (2 min)

Phase 1 (Critical doc rewrites) — AFTER understanding current UI
  ├── 1.1 USER_GUIDE_ADMIN.md (60-90 min)
  ├── 1.2 USER_GUIDE_OPERATOR.md (30 min)
  └── 1.3 README_SETUP.md (20 min)
```

**Recommended**: Phases 2-5 can be done in a single commit. Phase 1 needs careful work and should be its own commit(s).

---

## Verification Checklist

After all changes:
- [x] `grep -r "v2.1.0" docs/ README_SETUP.md` returns 0 results in customer-facing files
- [x] `grep -r "v3.4.0" docs/` returns 0 results (all bumped to v3.5.0)
- [x] README.md has no broken image references
- [ ] `placeholder.png` reference removed or replaced
- [ ] CORS origins in `api.py` have no dev-only entries
- [ ] `test_rtsp.py` not in project root
- [ ] `.env.example` exists and all env vars are valid
- [ ] ROADMAP.md has v3.5.0 in COMPLETED list
- [ ] Outdated docs moved to `docs/archive/`
- [ ] `ruff check .` passes on changed Python files
- [ ] `pytest tests/ -q` passes
- [ ] All internal markdown links verified (anchor links, file references)
- [ ] Regenerate PDFs from updated .md files (if tooling available)
