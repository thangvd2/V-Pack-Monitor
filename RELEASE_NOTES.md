# Lịch Sử Cập Nhật & Phát Hành (Release Notes)

> **Tác giả:** VDT - Vũ Đức Thắng | [GitHub](https://github.com/thangvd2)

## [v3.3.2] - 2026-04-22 (Performance & Cleanup) 🧹 PATCH RELEASE

### 🧹 Cleanup & Refactoring
- **Post-Release Cleanups (PR #40)**:
  - **Auto-remove broken cam2 path**: Added a MediaMTX health check monitor to detect unsupported/offline secondary cameras and gracefully stop re-registering them, stopping EOF log spam.
  - **Auto-migrate deprecated _sim modes**: Implemented a lifespan DB migration script to seamlessly convert deprecated `pip_sim` and `dual_file_sim` modes to standard modes without breaking existing station configurations.
  - **Remove version headers**: Cleaned up the file headers of 13 `.py` and 7 `.jsx` files by removing hardcoded version strings. Refactored build scripts to rely solely on the entry points, reducing noisy PR diffs.
- **Bump Version Cleanup (PR #38)**: Cleaned up the versioning script.

### ⚡ Performance & Testing
- **Pytest Performance Optimization (PR #39)**:
  - Patched `bcrypt` hashing rounds from 12 to 4 strictly for tests via `conftest.py` fixture.
  - Monkeypatched `video_worker._SHUTDOWN_TIMEOUT` down to 0.1s during test teardowns to prevent 60-second polling delays.
  - Reduced local pytest suite execution time from ~250 seconds down to ~40 seconds!

## [v3.3.1] - 2026-04-22 (Bugfixes & Cleanup) 🐛 PATCH RELEASE

### 🐛 Bug Fixes
- **Barcode Overwrite**: Sửa lỗi hiển thị mã vận đơn bị ghi đè im lặng khi quét mã mới trong lúc đang ghi hình, bổ sung cảnh báo tức thời trên UI và âm báo tự động.
- **Database FK Error**: Sửa lỗi Foreign Key cản trở việc xóa trạm thao tác (Station) nếu trạm đó từng có lịch sử phiên làm việc (bỏ điều kiện `status = 'ACTIVE'`).
- **Windows CI Compat**: Viết lại `pre-push` hook bằng Python với encoding `utf-8` để xử lý triệt để lỗi không tương thích bash script trên Windows.

### 🧹 Cleanup & Refactoring
- **Remove _sim modes**: Xóa bỏ hoàn toàn các chế độ giả lập (`pip_sim`, `dual_file_sim`) gây nhầm lẫn trên giao diện và backend, tự động fallback về SINGLE cho các cấu hình camera đơn giản.
- **Gitattributes Normalize**: Bổ sung tệp `.gitattributes` bắt buộc `LF` line endings cho text files, khắc phục dứt điểm lỗi perpetual diff của Prettier trên Windows.

### 📊 Stats
- **Total tests**: 323 (+1 new test cho edge case xoá station). All tests green.

## [v3.3.0] - 2026-04-19 (Phase 3 Infrastructure & Pydantic v2 Migration) 🚀 MINOR RELEASE

### 🏗️ Infrastructure & Refactor
- **Monolithic Function Refactor**: Tách hàm khổng lồ `_handle_scan_locked` (200+ dòng) trong `routes_records.py` thành 3 module-level helpers: `_handle_scan_start`, `_handle_scan_stop`, và `_handle_scan_exit`. Tăng cường khả năng đọc hiểu và bảo trì code.
- **Pydantic v2 Migration**: 
  - Hoàn tất chuyển đổi tất cả API payload calls từ `payload.dict()` (v1) sang `payload.model_dump(exclude_none=True)` (v2).
  - Thay thế deprecated `__init__` constructor validation trong `routes_auth.py` bằng `@model_validator(mode="after")`.
- **Circular Imports Handle**: Khắc phục circular dependency `_MAX_RECORDING_SECONDS` giữa `api.py` và `recorder.py` an toàn.

### 🗑️ Dead Code & Cleanup
- Xoá triệt để các dead code cũ: `database.save_record()` và `database.get_records()` (đã thay thế bởi version v2).
- Xóa hàm dư thừa `auth.hash_password()` cùng các unit test liên đới (hiện đã dùng `bcrypt` trực tiếp).
- **Test Suite Cleanup**: Loại bỏ 12 dòng lặp `sys.path.insert` trong thư mục `tests/` nhờ cơ chế import của `conftest.py`.

### 🎨 Frontend UI
- **Native Custom Dialog**: Tích hợp `showConfirmDialog` từ `App.jsx` xuống `UserManagementModal.jsx`. Xóa bỏ `window.confirm` kém thẩm mỹ.
- **Vietnamese Localization**: Khắc phục lỗi hiển thị tiếng Việt (diacritics) trên tiêu đề Tooltips của `VideoPlayerModal.jsx`.

### 📊 Stats
- **Total tests**: 322 (removed outdated tests). All tests green.

## [v3.2.0] - 2026-04-18 (.ai-sync Protocol, Release Workflow, Enforcement Layers) 🚀 MINOR RELEASE

### 🤝 .ai-sync/ — Universal AI Tool Coordination Protocol
- **Single source of truth** for coordinating OpenCode (GLM-5.1) and Antigravity (Gemini) on the same project
- `sync.py` auto-generates `AGENTS.md` (OpenCode) and `.agents/rules/` (Antigravity) from shared `.ai-sync/` source files
- Validates 12,000 char Antigravity rule file limit, `--check` mode for CI
- **3 enforcement layers**: pre-commit hook, CI job, RULES.md #7

### 📋 Memory Architecture (Based on Z.AI Official Docs)
- **5 memory types**: Session, Project, Semantic, Episodic, Procedural — mapped to `.ai-sync/` file structure
- **10 best practices** from Z.AI analyzed and mapped to `.ai-sync/` implementation
- **Platform Feature Matrix**: verified which features belong to OpenCode, Antigravity, and Claude Code
- **Episodic memory format**: structured `Problem → Root Cause → Solution → Prevention` entries

### 🔧 Release Workflow Improvements
- Added **git tag + GitHub release** steps to release workflow — prevents forgetting after merge
- Updated both `.ai-sync/workflows/release.md` and `CONTRIBUTING.md`

### 🛡️ Other Fixes
- Fix `required_approving_review_count` in branch protection restore command (#16)
- Document release process lessons (sole-developer workaround, strict:false) (#15)

### Files Added
- `.ai-sync/` — 11 source files (CONTEXT, RULES, MEMORY, TASKS, HANDOFF, README, sync.py, extensions/, workflows/)
- `.agents/` — 4 generated files (rules/, workflows/)
- `.pre-commit-config.yaml` — ai-sync-check hook added
- `.github/workflows/ci.yml` — ai-sync-check job added

## [v3.1.1] - 2026-04-17 (Security Fix, Test Coverage, Code Quality Tooling) 🔒 PATCH RELEASE

### 🔒 Security
- **Download endpoint station access check**: OPERATOR phải có active session trên trạm sở hữu record mới được download. ADMIN bypass (toàn quyền). Trước đó bất kỳ user xác thực nào cũng có thể download bất kỳ record nào bằng cách đoán record_id.

### 🧪 Test Coverage
- **Test `test_timer_cancelled_on_exit` fixed**: Dùng spy pattern (`MagicMock(wraps=timer.cancel)`) thay vì pre-cancel — verify đúng EXIT path cancel timers.
- **Test `test_timers_cancelled_on_shutdown`**: Verify tất cả timers cancelled và dicts cleared trên shutdown.
- **Test `test_auto_stop_sets_failed_when_queue_full`**: Verify FAILED status + SSE notification khi `submit_stop_and_save` return False (queue full).
- **4 download authorization tests**: Operator own station, operator other station, admin bypass, operator no session.

### 🛡️ Code Quality
- **Prettier setup**: Formatting enforcement cho toàn bộ web-ui (indent, quotes, commas, spacing). `npm run lint` now includes Prettier check. Pre-commit hook auto-formats on commit.
- **ESLint + Prettier integration**: `eslint-config-prettier` tắt conflicting rules.
- **Branch protection enforcement**: 3 layers — GitHub branch protection (enforce_admins), pre-push hook (`.git-hooks/check-protected-branch.sh`), AGENTS.md checklist.
- **Anti-false-positive review rules**: Dependency chain tracing, FOR/AGAINST evidence, 2-pass review process in AGENTS.md.
- **Mandatory user confirmation**: AI agents must ask before merging any PR.
- **SetupModal cleanup**: `conflictTimerRef` cleared on unmount.

### 📊 Stats
- **6 new tests** (total: 312)
- **8 source files formatted** by Prettier
- **5 PRs merged**: #10, #11, #12, #13

## [v3.1.0] - 2026-04-17 (Auto-Stop Recording, Notification Sounds, Quality Enforcement) 🚀 MINOR RELEASE

### ⏱️ Auto-Stop Recording (10 min max)
- **Timer auto-stop**: Recording tự động dừng và lưu sau 10 phút nếu operator không scan STOP — tránh file video khổng lồ khi operator bỏ quên.
- **9-minute warning**: SSE event `recording_warning` emit ở phút thứ 9, frontend hiển thị toast đếm ngược + âm thanh cảnh báo.
- **FFmpeg hard cap**: `-t 600` trên tất cả recording modes (SINGLE, DUAL_FILE, PIP) — belt-and-suspenders safety.
- **Race condition safe**: Timer verify `record_id` trước khi stop — không bao giờ stop nhầm recording khác.
- **Clean cleanup**: Timer cancel trên STOP/EXIT/shutdown, warning timer cancel đúng cách, `_recording_start_times` cleanup đầy đủ.
- **11 regression tests**: Coverage cho race conditions, timer leaks, warning guards, cleanup paths.

### 🔔 Notification Sounds
- **Web Audio API synthesized sounds** — không cần file MP3 bên ngoài, zero dependencies.
  - Ascending beep (440→880Hz): barcode scan → recording bắt đầu
  - Descending beep (880→440Hz): STOP scan / auto-stop → recording kết thúc
  - Two-tone chime (C5→G5): video processing hoàn tất
  - Double-beep (660Hz square): cảnh báo 60 giây trước auto-stop
- **600ms debounce** per sound type — không overlap khi nhiều SSE events đến cùng lúc.
- **Async AudioContext** với user gesture warmup — hoạt động trên Chrome, Firefox, Safari.

### 🛡️ Quality Enforcement
- **Pre-commit hooks**: ruff lint + format, detect-secrets, ESLint (frontend), pytest pre-push.
- **ruff.toml**: Line-length 120, F401/F841 strict — catch unused imports/variables mới.
- **ESLint 0 errors, 0 warnings**: Fix tất cả `react-hooks/exhaustive-deps` violations, `no-unused-vars` args pattern.
- **`requirements-dev.txt`**: Tách dev deps (pre-commit, ruff, pytest, httpx) khỏi production deps.
- **AGENTS.md**: Thêm mandatory pre-push review rule (self-review, test coverage, thread safety audit).
- **CONTRIBUTING.md**: Thêm commit hygiene rule — không mix formatting với logic changes.

### 🐛 Bug Fixes
- **showToast race condition**: Timeout ref cleanup đúng cách — không để toast cũ ghi đè toast mới.
- **Warning timer leak**: Warning timer được store và cancel đúng cách trên STOP/EXIT.
- **`_emit_recording_warning` guard**: Kiểm tra recording active trước khi emit SSE.
- **Shutdown timer cleanup**: Cancel tất cả recording timers trước khi dừng worker.
- **SetupModal `checkConflicts` hoisting**: Di chuyển lên trước `validate()` để giải quyết TDZ issue.
- **Regex escape**: `[\s:\-\.]` → `[\s:.-]` trong MAC address processing.

### 📊 Stats
- **43 files changed**, +1939/-711 lines
- **11 new tests** (`test_auto_stop_timer.py`)
- **1 new file** (`web-ui/src/utils/notificationSounds.js`, 179 lines)
- **Total tests**: 306 (was 305)

## [v3.0.0] - 2026-04-16 (Architecture Overhaul & Major Security Hardening) 🎉 MAJOR RELEASE

### 🏗️ Kiến Trúc Lớn
- **Route Module Decomposition:** Tách `api.py` monolith (~1500 dòng) thành 4 route modules chuyên trách, mỗi module export `register_routes(app)`:
  - `routes_auth.py` (235 dòng) — Auth + User CRUD + Session management
  - `routes_records.py` (436 dòng) — Scan, records, download, SSE, live preview
  - `routes_stations.py` (321 dòng) — Station CRUD + discovery + sessions
  - `routes_system.py` (915 dòng) — Settings, analytics, health, auto-update, CSV export
- **CI/CD Pipeline:** GitHub Actions tự chạy pytest + frontend build + ruff lint trên mỗi push/PR nhắm vào `master`/`dev`.
- **Development Workflow:** Thêm `AGENTS.md` (AI agent rules), `CONTRIBUTING.md` (quy trình phát triển), PR template.
- **Unit Test Suite:** 305 tests covering auth, API routes, database, encryption, FTS5 search, video worker, network, cloud sync, security regression, edge cases.

### 🔒 Security Hardening — 111 Issues Resolved (from v2.4.2 → v3.0.0)

#### database.py (34 issues)
- **Fernet Encryption:** Thay XOR + base64 bằng `cryptography.fernet.Fernet` cho sensitive settings. Auto-migration v1→v2 trong `init_db()`.
- **Foreign Key Enforcement:** `PRAGMA foreign_keys=ON` trên mỗi connection. Orphan cleanup chạy khi startup.
- **6 New Indexes:** Tối ưu query performance cho `records`, `stations`, `sessions`, `audit_log`.
- **WAL Mode:** Write-Ahead Logging cho concurrent read/write.
- **`get_connection()` Factory:** Centralized connection creation với PRAGMA enforcement.
- **CHECK Constraints:** Validate data tại DB level.
- **Bounded Inputs:** Tên station, username, waybill code có max length.
- **Deprecation Docstrings:** Cảnh báo cho các hàm legacy.

#### api.py (32 issues)
- **Per-Concern Thread Locks:** `_recorders_lock`, `_streams_lock`, `_station_locks_lock`, `_cache_lock`, `_login_attempts_lock` — thay thế single giant lock.
- **Path Traversal Prevention:** Validate semua file paths chống zip slip.
- **HTTP Status Codes:** 401/403/422/429/413/503 thay vì generic 400/500.
- **Pydantic Field Validation:** Tất cả API payloads có type + constraint validation.
- **Admin Self-Lock Prevention:** Admin không thể tự lock/khoá tài khoản mình.
- **Upload Size Limit:** Credentials upload giới hạn 1MB.
- **SSRF Prevention:** `/api/ping` chỉ chấp nhận private IP.
- **SSE Max 50 Clients:** Chống resource exhaustion.
- **Failed Login Audit Trail:** Log mọi login thất bại vào audit log.
- **Background Recovery Thread:** Crash recovery chạy độc lập, không block startup.
- **`sys.exit(0)`:** Thay `os._exit(0)` cho graceful shutdown.
- **Tempfile for Restart Scripts:** Tạo restart script trong temp directory, tự cleanup.

#### recorder.py (3 issues)
- **Waybill Code Sanitization:** `re.sub(r'[^\w\-.]', '_', ...)` chống path injection.
- **`_stopped` Flag Reset:** Fix reuse bug khi recorder stop/start lại.
- **Transcode Error Logging:** Log chi tiết khi HEVC→H.264 transcode thất bại.

#### video_worker.py (3 issues)
- **Bounded Queue:** `_MAX_PENDING=10` — giới hạn tasks chờ xử lý.
- **Callback Pattern:** `_decrement_callback` tránh circular import với api.py.
- **Submit/Shutdown Race:** Fix race condition khi submit task đúng lúc shutdown.

#### auth.py (3 issues)
- **`int(user_id)` ValueError Handling:** Tránh crash khi JWT payload bị corrupt.
- **Revocation Error Logging:** Log lỗi khi token revocation thất bại.
- **Expiry Comment:** Document token expiry behaviour.

#### cloud_sync.py (4 issues)
- **Path Validation in Zip:** Kiểm tra mỗi entry trong zip file chống zip slip.
- **GDrive Credentials Caching:** Cache parsed credentials, không parse mỗi lần.
- **Concurrency Lock:** Thread lock cho cloud sync operations.
- **Direct sqlite3.connect TODO:** Document cần refactor sang database.py.

#### telegram_bot.py (3 issues)
- **Bot Token Caching:** Cache bot instance với 5 phút TTL.
- **Exponential Backoff Polling:** Tránh spam khi Telegram API down.
- **Direct sqlite3.connect TODO:** Document cần refactor sang database.py.

#### network.py (3 issues)
- **ThreadPoolExecutor for LAN Scan:** Thay sequential ping bằng parallel scanning.
- **Private IP Validation:** Validate IP trước khi scan.
- **Fallback Comment:** Document fallback behaviour.

#### Frontend (27 issues)
- **AbortController:** Cancel pending fetch khi component unmount.
- **Fetch+Blob for Downloads:** Thay `window.open()` bằng authenticated download.
- **Custom Confirm Dialog:** Thay `window.confirm()` bằng styled modal.
- **Toast Replacing alert():** Tất cả `alert()` thay bằng toast notification.
- **Station Switch Lock Flag:** Ngăn double-click khi chuyển trạm.
- **`doChangePassword()` Extraction:** Tách logic đổi mật khẩu ra function riêng.
- **SSE Stable Dependencies:** `useCallback`/`useMemo` cho SSE handler, tránh reconnect loop.
- **`config.js`:** Shared `API_BASE` constant, không hardcode URL.
- **Named Constants:** Magic numbers → named constants (`MAX_LOGIN_ATTEMPTS`, etc.).
- **useMemo Optimisation:** Memo expensive computations.
- **Version Cleanup:** Remove dead version-related code.
- **ErrorBoundary Component:** Catch React render errors gracefully.
- **Search Debounce 300ms:** Tránh spam API khi typing.
- **Axios Timeout 15s:** Default timeout cho tất cả API calls.

### 📁 Files Thay Đổi
- `api.py`: Giảm từ ~1500 → ~553 dòng (routes tách ra). Thread locks, status codes, validation.
- `routes_auth.py` (mới): Auth + User CRUD routes.
- `routes_records.py` (mới): Scan, records, download, SSE routes.
- `routes_stations.py` (mới): Station CRUD + sessions + discovery routes.
- `routes_system.py` (mới): Settings, analytics, health, update routes.
- `database.py`: Fernet encryption, FK enforcement, indexes, WAL, `get_connection()`.
- `recorder.py`: Path sanitization, `_stopped` flag fix.
- `video_worker.py`: Bounded queue, callback pattern, shutdown race fix.
- `auth.py`: ValueError handling, revocation logging.
- `cloud_sync.py`: Zip path validation, credentials caching, concurrency lock.
- `telegram_bot.py`: Token caching, exponential backoff.
- `network.py`: ThreadPoolExecutor, IP validation.
- `web-ui/src/App.jsx`: 27 frontend hardening issues.
- `web-ui/src/config.js` (mới): Shared API_BASE constant.
- `tests/`: 305 tests (108 new).
- `AGENTS.md` (mới): AI agent rules.
- `CONTRIBUTING.md` (mới): Development workflow.
- `.github/workflows/ci.yml` (mới): CI/CD pipeline.
- `.github/pull_request_template.md` (mới): PR template.

### ⚠️ Breaking Changes
- **Encryption Migration:** XOR v1 → Fernet v2. Auto-migration chạy trong `init_db()`. Không rollback được.
- **API Status Codes:** Nhiều endpoint trả về status codes mới (401/403/422/429 thay vì 400). Frontend cần handle đúng.

---

## [v2.4.2] - 2026-04-15 (Security & Stability Audit — 22 Issues)

### 🔒 CRITICAL Fixes
- **FTS5 MATCH Crash Guard:** FTS5 `MATCH` query với ký tự đặc biệt → crash. Thêm try/except fallback sang `LIKE` query.
- **SSE Stale Closure Fix:** SSE handler dùng ref (`searchTermRef.current`) thay vì closure capture — filter đúng khi search term thay đổi.
- **Timezone Store UTC:** `recorded_at` lưu UTC trong DB, convert sang localtime khi query. Fix analytics sai 7 giờ (UTC+7).

### 🛡️ HIGH Fixes
- **Zip Slip Prevention:** Validate extract path trong auto-update zip.
- **Login Cleanup Threshold:** Giảm từ 1000 → 100 entries dọn login attempts.
- **Production Update Zip Integrity:** Check zip file size trước khi extract.
- **`_parse_semver` Pre-release Tags:** Version comparison handle `v3.0.0-beta` đúng.
- **SSE Queue Bounded:** `maxsize=100` cho SSE queue, chống memory leak.

### 🔧 MEDIUM Fixes
- **CORS Explicit Methods/Headers:** Thu hẹp CORS cho phép methods/headers cụ thể.
- **`activeStationId` Init Null:** Fix undefined state khi chưa chọn trạm.
- **ErrorBoundary Component:** Catch React render errors.
- **Search Debounce 300ms:** Tránh spam API.
- **Axios Timeout 15s:** Default timeout cho API calls.

### 📁 Files Thay Đổi
- `api.py`: FTS5 crash guard, SSE stale fix, timezone UTC, zip slip, login cleanup, CORS, SSE bounded.
- `database.py`: UTC storage, `localtime` conversion in queries.
- `web-ui/src/App.jsx`: ErrorBoundary, search debounce, axios timeout, CORS.
- `tests/`: 8 tests updated cho new validation/status codes.

---

## [v2.4.1] - 2026-04-14 (Semver Fix)

### 🐛 Bug Fix
- **Semver Version Comparison:** `_parse_semver()` so sánh version đúng — `v2.4.0` > `v2.3.0` (trước đó compare string `v2.4.0` < `v2.3.0` sai).
- **Bump VERSION:** `v2.4.0` → `v2.4.1`.

### 📁 Files Thay Đổi
- `api.py`: `_parse_semver()` function.
- `VERSION`: `v2.4.1`.

---

## [v2.3.0] - 2026-04-13 (Auto-Update System)

### 🔄 Tính Năng Lớn
- **Auto-Update System:** Admin bấm 1 nút → server tự update + restart. Hỗ trợ 2 mode:
  - **Dev Mode** (phát hiện bằng `.git/` folder): `git stash` → `git pull` → `npm install` → `npm run build` → restart
  - **Production Mode** (không có `.git/`): Download GitHub Release ZIP → backup DB → extract (skip recordings/venv/bin) → pip install → npm build → restart
- **Version Badge:** Header hiển thị version hiện tại (ADMIN only). Badge vàng khi có bản mới, click → modal xác nhận.
- **Real-time Progress:** SSE push progress events (checking → downloading → extracting → installing → building → restarting) với progress bar.
- **Auto-check on startup:** ADMIN login → tự động check bản mới qua `GET /api/system/update-check` (cache 1 giờ).
- **DB Backup & Rollback:** Production mode backup `packing_records.db` trước khi update. Restore backup nếu update thất bại.
- **Cross-platform Restart:** Windows (`_update_restart.bat` tự xoá) + macOS/Linux (`_update_restart.sh` tự xoá).

### 🔒 Hardening (24 issues fixed qua code review)
- **CRITICAL:** `os._exit(0)` trong background thread thay vì `sys.exit(0)` từ threadpool worker — tránh process không chết
- **CRITICAL:** Graceful shutdown recorder + video_worker trước khi restart — tránh corrupt video
- **CRITICAL:** HTTP response trả về TRƯỚC khi restart — tránh client nhận connection error
- **CRITICAL:** `_update_lock` + `_is_updating` chống concurrent update
- **HIGH:** `git stash pop` khi `git pull` thất bại — không mất local changes
- **HIGH:** `_do_graceful_restart` bọc `try/finally` — luôn `os._exit(0)`, không bao giờ lock update
- **MEDIUM:** Auto-detect git branch (`_get_git_branch()`) thay vì hardcoded `master`
- **MEDIUM:** Cache update-check 1 giờ (`_update_check_ttl=3600`) — tránh GitHub API rate limit
- **MEDIUM:** `tag[1:] if tag.startswith('v')` thay vì `tag.lstrip('v')` — tránh strip sai
- **MEDIUM:** Check npm availability trong production → skip build gracefully nếu không có Node.js
- **MEDIUM:** SSE `time.sleep(1.5)` delays — đảm bảo event delivery trước khi process exit
- **LOW:** Temp restart scripts tự xoá (`del "%~f0"` / `rm -- "$0"`)
- **LOW:** Frontend: không reset `updating` state khi network error (server đang restart)
- **LOW:** Frontend: reset `updateProgress` khi mở modal lần mới
- **LOW:** DB `.bak` cleanup sau update thành công

### 🏗️ Kiến Trúc
- **`VERSION`** (mới): File chứa version string (`v2.3.0`), đọc bởi backend, commit vào repo.
- **`api.py`**: 2 endpoints mới, `_get_git_branch()`, `_update_dev()`, `_update_production()`, `_do_graceful_restart()` (try/finally), SSE `update_progress` events, cache 1 giờ, concurrent update lock.
- **`web-ui/src/App.jsx`**: Version badge, Update Modal với progress bar, SSE `update_progress` listener, auto-reload sau restart.
- **`.gitignore`**: Thêm `*.db.bak` (DB backup không commit).

### 📁 Files Thay Đổi
- `VERSION` (mới): Version tracking file
- `api.py`: 2 update endpoints + restart mechanism + SSE progress + cache + lock
- `web-ui/src/App.jsx`: Version badge + update modal + SSE listener
- `.gitignore`: Thêm `*.db.bak`
- `docs/plans/18_auto_update_plan.md`: Trạng thái → COMPLETED

## [v2.2.4] - 2026-04-12 (Security Hardening — 26 Vulnerabilities Fixed)

### 🔒 CRITICAL Fixes
- **VULN-01:** Xóa static mount `/recordings/` — video download qua authenticated endpoint `/api/records/{id}/download/{idx}` (JWT token qua query param, hỗ trợ `<video>` tag)
- **VULN-02:** CORS thu hẹp — auto-detect local IP, chỉ cho phép `localhost` + `127.0.0.1` + LAN IP
- **VULN-03:** Default admin password `admin/08012011` — thêm cờ `must_change_password`, bắt buộc đổi password lần đầu login, không in password ra console, không thể đóng modal
- **VULN-04:** OPERATOR không xem được `safety_code` (camera password) — chỉ ADMIN thấy

### 🛡️ HIGH Fixes
- **VULN-05:** Login rate limiting — 5 lần sai / 5 phút / IP
- **VULN-06:** JWT token revocation — thêm bảng `revoked_tokens`, logout thu hồi token bằng `jti`, cleanup expired tokens khi startup
- **VULN-07:** SSE `/api/events` yêu cầu authentication (token qua query param)
- **VULN-08:** Credentials upload validate JSON structure trước khi ghi file
- **VULN-09:** SQL injection prevention — whitelist column names trong `update_station_ip`
- **VULN-10:** Sensitive settings mask `"****"` trong GET response, preservation check khi PUT

### 🔧 MEDIUM Fixes
- **VULN-12:** `/api/reconnect-status` yêu cầu authentication
- **VULN-13:** Server-side password validation ≥ 6 ký tự (Pydantic validator)
- **VULN-14:** Session heartbeat kiểm tra ownership — không heartbeat session của user khác
- **VULN-15:** Sensitive settings (S3_SECRET_KEY, TELEGRAM_BOT_TOKEN) encrypted at rest trong SQLite (XOR + base64, key derive từ JWT secret)
- **VULN-16:** Telegram bot token không nhúng trong f-string URL
- **VULN-18:** Generic error messages thay raw exception trong cloud sync + delete record

### 📝 LOW Fixes
- **VULN-22:** JWT leeway giảm 30s → 5s
- **VULN-25:** Barcode input length limit 200 ký tự
- **VULN-26:** FFmpeg command lines redact credentials (regex `://***@`)

### ⚠️ Not Applicable / Deferred
- **VULN-11:** TLS/HTTPS — cần nginx reverse proxy (env var `VPACK_HOST` để customize bind host)
- **VULN-17:** Không có RTSP URL log statements — đã redact qua VULN-26
- **VULN-19:** Sequential IDs — không ưu tiên, ảnh hưởng toàn bộ schema
- **VULN-21:** CSRF — đã fixed khi CORS fixed

### 🐛 Side Effect Fixes (Post-Audit)
- **Settings mask preservation:** Đổi mask thành `"****"` (all-star) + check chính xác, tránh corrupt sensitive settings khi save
- **Video playback auth:** Download endpoint nhận token qua query param (hỗ trợ `<video>` tag không gửi header)
- **First-run crash:** `os.makedirs("recordings")` chạy trước DB access, tránh crash lần đầu clone
- **CORS LAN access:** Auto-detect local IP qua UDP socket → thêm vào allowed origins

### 📁 Files Thay Đổi
- `api.py`: 15 vulnerabilities fixed + authenticated download endpoint + rate limiting + SSE auth + mask settings + CORS auto-detect
- `auth.py`: JWT `jti` claim + token revocation + leeway fix
- `database.py`: `revoked_tokens` table + `must_change_password` column + encrypt at rest + `get_record_by_id` + SQL whitelist + makedirs guard
- `telegram_bot.py`: Token không nhúng URL literal
- `web-ui/src/App.jsx`: SSE token auth + force change password modal + authenticated video URL with token
- `web-ui/src/VideoPlayerModal.jsx`: Authenticated download URL

## [v2.2.3] - 2026-04-12 (Record Stream Toggle)

### 🎥 Record Stream Toggle
- **"Rec: 1080p / 480p" toggle button** (ADMIN only) — chọn main-stream hoặc sub-stream cho recording
- **Backend:** `RECORD_STREAM_TYPE` setting lưu DB, recording flow đọc setting
- **Bug fix:** `delete_station` race condition (`del` → `pop`)

## [v2.2.2] - 2026-04-12 (Security & Stability Patch)

### 🔒 Security Fixes (CRITICAL)
- **JWT Secret auto-generate:** Xóa hardcoded fallback `"vpack-monitor-secret-key-2026-change-in-production"`. Secret key giờ tự generate random 64-char hex (`secrets.token_hex(32)`), lưu trong DB `system_settings` table. Hỗ trợ env var `VPACK_SECRET` cho deployment chuyên nghiệp. (auth.py)
- **`GET /api/stations` auth required:** Thêm `CurrentUser` dependency — fix leak toàn bộ camera IPs, safety codes, MAC addresses cho unauthenticated users. (api.py:666)
- **Password reset via request body:** Đổi từ query param `?password=xxx` (bị log trong access log, browser history, proxy) sang Pydantic model `ResetPasswordPayload`. Frontend gửi password trong request body. (api.py:632-640, UserManagementModal.jsx:206-207)
- **CSV export Blob download:** Thay `window.open(url + token)` bằng `axios.get` + Blob download. Auth qua Authorization header (tự động), không lộ JWT token trong URL. Backend dùng `CurrentUser` thay vì manual token parsing. (Dashboard.jsx:125-142, api.py:1190-1195)

### 🛡️ Data Integrity Fixes (HIGH)
- **`.ts` temp file retained on transcode failure:** Khi HEVC→H.264 transcode thất bại, raw `.ts` file được rename thành `.FAILED.ts` thay vì bị xóa — cho phép manual recovery, chống mất dữ liệu vĩnh viễn. (recorder.py:374-389)
- **`video_worker.shutdown(wait=True)`:** Đổi từ `wait=False` → `wait=True` — server shutdown chờ video đang xử lý hoàn tất, chống file corrupt. (video_worker.py:150)
- **UTC/local timestamp consistency:** Tất cả analytics queries (hourly, trend, stations-comparison, CSV export, cleanup) dùng `datetime('now', 'localtime')` đồng bộ với `datetime.now()` (Python local time) dùng khi insert records. Tránh xóa record sớm 7 giờ (offset UTC+7). (database.py)

### 🔧 Compatibility Fixes (CRITICAL)
- **Windows ping command:** Camera reachability check dùng `ping -n 1 -w 1000` (Windows) hoặc `ping -c 1 -W 1` (Linux/macOS) dựa trên `platform.system()`. Fix camera luôn hiển thị "Unreachable" trên production Windows. (api.py:1396-1407)

### 🐛 Bug Fixes (HIGH/LOW)
- **MediaMTX re-register on IP change:** `update_url()` giờ gọi `_mtx_remove_path()` + `_mtx_register()` khi URL thay đổi. Fix live view stale sau khi camera IP update. (api.py:198-200)
- **SSE stale closure fix:** SSE handler dùng `searchTermRef.current` (ref) thay vì `searchTerm` (closure capture). Records list filter đúng khi search term thay đổi mà không cần reconnect SSE. (App.jsx:204-205, 289, 298, 305, 312)

### 🌐 Frontend
- **UTF-8 BOM for CSV export:** Thêm `\ufeff` BOM vào đầu file CSV — Excel Windows hiển thị đúng font tiếng Việt (Mã vận đơn, Trạm, Trạng thái...). (api.py:1217)
- **Missing `recharts` dependency:** Thêm `recharts` vào `package.json` — fix build error `rolldown failed to resolve import "recharts"`.

### 📁 Files Thay Đổi
- `auth.py`: `_load_or_create_secret()` — auto-generate JWT secret, lưu DB
- `database.py`: `set_setting()` function mới, `localtime` cho tất cả analytics queries + cleanup
- `api.py`: Stations auth, Windows ping, MediaMTX re-register, password body, CSV auth+BOM
- `recorder.py`: `transcode_ok` flag, `.FAILED.ts` recovery
- `video_worker.py`: `shutdown(wait=True)`
- `web-ui/src/App.jsx`: `searchTermRef` cho SSE handler
- `web-ui/src/UserManagementModal.jsx`: Password gửi qua request body
- `web-ui/src/Dashboard.jsx`: Blob download thay vì `window.open` + token
- `web-ui/package.json`: Thêm `recharts`

---

## [v2.2.1] - 2026-04-11 (Mobile Responsive Phase 1 & Critical Bug Fix)

### 🐛 Critical Bug Fix
- **Restore missing useState declarations:** Commit `82b5c7c` ("dead code cleanup") đã vô tình xoá 16 `useState` declarations khỏi `App.jsx` (chỉ nên xoá 3: `diskHealth`, `showSystemHealth`, `SystemHealth` import). Các state bị xoá nhầm bao gồm: `stationStatuses`, `videoModalOpen`, `selectedVideo`, `showUserModal`, `showUserDropdown`, `showChangePassword`, `changePasswordForm`, `changePasswordError`, `changePasswordSuccess`, `mtxAvailable`, `toast`, `stationAssigned`, `activeSessionId`, `pipCamSwap`. Gây crash `ReferenceError` khi load UI sau login. Đã restore tất cả.

### 📱 Mobile Responsive — Phase 1 (CSS-only)
- **Login page:** Responsive padding (`p-4 md:p-8`), `text-base` inputs (iOS zoom fix), `min-h-[44px]` touch targets.
- **Header:** Compact 2-row layout trên mobile, search full-width (`order-last md:order-none`), user info rút gọn trên small screens.
- **Live view:** Aspect ratio `4:3` trên mobile (taller), `16:9` trên desktop.
- **Barcode simulator:** Mobile-first inputs (larger, 44px touch targets), `inputMode="text"` + `enterKeyHint="send"`, buttons "Ghi" / "STOP" rút gọn trên mobile.
- **History:** `showAllRecords` — hiện 3 records + nút "Xem thêm" (chỉ mobile), full list trên desktop.
- **Grid view toggle + Dashboard button:** `hidden md:flex` — ẩn trên mobile.
- **Touch targets:** `min-h-[44px]` trên tất cả interactive elements.

### 🔧 Other Changes
- **PIP overlay position:** FFmpeg overlay filter `y=10` (góc trên phải) → `y=main_h-overlay_h-10` (góc dưới phải). Camera 2 giờ hiển thị đúng vị trí góc dưới bên phải trong cả live view và video ghi lại.
- **Live PIP wrapper:** `w-full h-full relative` → `absolute inset-0` — fix positioning trong flex container.
- **`start.sh` + `Start V-Pack Monitor.command`:** Thêm `ulimit -n 4096` (tăng file descriptor limit cho MediaMTX + FFmpeg).

### ⚠️ Known Issue
- `showAllRecords` giới hạn 3 records trên CẢ desktop lẫn mobile — cần fix chỉ limit trên mobile.

---

## [v2.2.0] - 2026-04-11 (Video Pipeline Reliability & UI Refactor)

### 🎥 Video Pipeline — Xử Lý Đa Đơn Hàng
- **Processing Counter:** Thay `_processing_stations` (set) bằng `_processing_count` (dict counter) — cho phép operator quét mã mới ngay khi nhấn STOP, không cần chờ video đơn trước xử lý xong.
- **Station Lock:** Thêm `_station_locks` — mỗi trạm có `threading.Lock` riêng, ngăn double-scan tạo 2 records khi barcode scanner gửi 2 lần liên tiếp.
- **VideoWorker Cleanup:** Bỏ `active_waybills.pop()` / `active_record_ids.pop()` khỏi worker thread — chống race condition khi đơn mới bắt đầu trước khi đơn cũ convert xong.

### 🔄 SSE Single Source of Truth
- **SSE là nguồn duy nhất:** `packingStatus` chỉ thay đổi qua SSE events, HTTP scan response chỉ set `activeRecordIdRef` (optimistic update cho guard).
- **Strict Record ID Guard:** SSE handler chỉ reset state khi `data.record_id === activeRecordIdRef.current`. SSE events của đơn cũ bị ignore hoàn toàn khi đang ghi đơn mới.
- **SSE Polling 500ms → 100ms:** Giảm delay event delivery xuống 5 lần.

### 🎨 UI Refactor — Header Tối Giản
- **Header cleanup:** Xoá Analytics badge, Storage badge, System Health button khỏi header. Chuyển tất cả vào Dashboard.
- **Dashboard 2-tab:** Tab "Thống kê" (Analytics + Charts) + Tab "Sức khỏe hệ thống" (SystemHealth component).
- **Admin menu vào User Dropdown:** Cloud Sync, Cài đặt Trạm, Quản lý người dùng chuyển từ header buttons sang user dropdown menu.
- **Uniform button sizes:** Tất cả header elements đồng nhất `h-10` + `rounded-xl`.

### 🐛 Bug Fixes
- **Double-scan tạo 2 records:** Station lock serialize tất cả scan requests cho cùng 1 trạm.
- **Status nhảy loạn ở đơn thứ 3:** `activeRecordIdRef` guard strict match — SSE events cũ bị block hoàn toàn.
- **Toast "Đang xử lý video" khi scan mới:** Xoá `_processing_count` check khỏi scan flow — operator luôn có thể bắt đầu đơn mới.
- **Đơn B stuck "Đang ghi hình" khi A đang xử lý:** Chuyển `database.update_record_status(PROCESSING)` + SSE PROCESSING lên main thread (trước khi queue VideoWorker). Record B chuyển "Đang xử lý" ngay lập tức khi STOP, không cần chờ A convert xong.
- **Toast thỡ "Bắt đầu ghi hình..." khi scan mới:** Xoá toast cho status `recording` — chỉ hiện toast khi có error thực sự. SSE RECORDING lo việc update UI.
- **Barcode scanner cho ADMIN:** ADMIN không còn nhận keypress từ barcode scanner (tránh tạo records).
- **CSV Export 401:** `window.open()` không gửi Authorization header → truyền JWT token qua query param.
- **System Health Permission:** OPERATOR không còn thấy được tab "Sức khỏe hệ thống" (ADMIN only).
- **Disk Usage sai số liệu:** `psutil.disk_usage("/")` → `psutil.disk_usage("recordings")` — hiện đúng partition chứa video.
- **Dead code cleanup:** Xoá `showSystemHealth` state, `diskHealth` state, `fetchDiskHealth`, `SystemHealth` import khỏi App.jsx.

### 📁 Files Thay Đổi
- `api.py`: `_processing_stations` → `_processing_count`, `_station_locks`, SSE `waybill` field, SSE polling 100ms, PROCESSING status update trong main thread
- `video_worker.py`: Helper functions `_decrement_processing()` / `_notify_sse_safe()`, bỏ `active_waybills.pop()`, bỏ duplicate PROCESSING update
- `web-ui/src/App.jsx`: `activeRecordIdRef`, SSE strict guard, header cleanup, admin dropdown menu, xoá toast cho recording
- `web-ui/src/Dashboard.jsx`: 2-tab layout, SystemHealth integration

## [v2.1.0] - 2026-04-10 (Station Assignment & Bug Fixes)

### 🔐 Tính Năng Lớn
- **Station Assignment cho OPERATOR:** Sau khi đăng nhập, OPERATOR phải chọn trạm làm việc. Hiển thị trạng thái 🟢 Trống / 🔴 Đang dùng. Trạm occupied không thể chọn. ADMIN tự do xem tất cả.
- **Session Lifecycle:** Acquire → Heartbeat 30s → Release. Session expire sau 90s nếu mất heartbeat. Auto-expire tất cả sessions khi server restart.
- **PIP Click-to-Swap:** Click vào PIP overlay để swap camera chính/phụ. Badge ⇄ chỉ thị swap.

### 📊 Audit & Monitoring
- **6 Audit Actions mới:** LOCK_USER, UNLOCK_USER, SETTINGS_UPDATE, STATION_CREATE, STATION_UPDATE, STATION_DELETE. Tổng 16 actions được log.
- **Periodic Audit Cleanup:** Dọn audit log cũ (>90 ngày) mỗi 24 giờ, không chỉ lúc startup.
- **Station Status API:** `GET /api/sessions/station-status` — trả về tất cả trạm + occupied/free + username.

### 🔧 Tách Trạng Thái Hiển Thị
- **Live View:** Hiển thị trạng thái quy trình đóng hàng — 🔴 "Đang đóng hàng: [MÃ VẠCH]" / 🟢 "Sẵn sàng". Quét STOP → quay về Sẵn sàng ngay.
- **History Cards:** Hiển thị trạng thái luồng video — "Đang ghi hình" / "Đang xử lý" / "Sẵn sàng" / "Lỗi" (tiếng Việt). SSE cập nhật realtime.

### 🐛 Bug Fixes
- **passlib → bcrypt:** Thay `passlib` (unmaintained) bằng `bcrypt` trực tiếp. Khắc phục crash trên Python 3.14.
- **MediaMTX Fallback:** Frontend hiển thị "📡 MediaMTX chưa khởi động" thay vì broken iframe "localhost refused to connect".
- **MTX Status API:** `/api/mtx-status` trả 503 (thay vì 200) khi MediaMTX down → frontend detect đúng.
- **MediaMTX Auto-Install:** `install_macos.sh` tự động tải MediaMTX v1.17.1. Config `api: true` bật Control API.
- **Data Load After Login:** Init fetch chuyển sang `useEffect([currentUser])` — data load sau khi login, không phải trước.
- **Barcode Popup:** Bỏ alert không cần thiết khi scan lại mã đang đóng. Alert chỉ hiện khi busy/processing.

### 📁 Files Thay Đổi
- `auth.py`: `passlib` → `bcrypt` trực tiếp
- `database.py`: 3 chỗ `passlib` → `bcrypt` + `cleanup_audit_log()` function mới
- `api.py`: 6 audit log calls, periodic cleanup, `GET /api/sessions/station-status`, `HTTPException` import
- `requirements.txt`: `passlib[bcrypt]` → `bcrypt>=4.0.0`
- `App.jsx`: Station selection screen, session flow, PIP swap, status separation, MediaMTX fallback
- `install_macos.sh` + `Install V-Pack Monitor.command`: Thêm bước download MediaMTX
- `bin/mediamtx/mediamtx.yml`: `api: true`
- `docs/plans/12_v2_roadmap_plan.md`: Mục 2.3.1 Station Assignment, mục 1.6 status separation
- `docs/plans/13_v3_roadmap_plan.md`: Audit gaps, PIP swap, RAM threshold notes

---

## [v2.0.0] - 2026-04-09 (System Health Dashboard) 🎉 MAJOR RELEASE

### 🏥 Tính Năng Lớn
- **System Health Dashboard:** Trang theo dõi sức khỏe hệ thống thời gian thực — CPU, RAM, Disk với progress bar + status indicators (OK/Warning/Critical).
- **FFmpeg Process Monitor:** Liệt kê tất cả FFmpeg processes đang chạy — PID, lệnh, CPU%, RAM%.
- **Camera Reachability:** Ping kiểm tra từng camera — hiển thị trạng thái 🟢 Reachable / 🔴 Unreachable.
- **Server Info:** Uptime, hostname, local IP.
- **Auto-refresh:** Polling mỗi 5 giây. ADMIN-only.

### 🏗️ Kiến Trúc
- **`SystemHealth.jsx`** (mới): Component dashboard sức khỏe với 3 API polling song song.
- **`api.py`**: 3 endpoints mới (`GET /api/system/health`, `GET /api/system/processes`, `GET /api/system/network-info`). Thêm `psutil`.
- **`requirements.txt`**: Thêm `psutil>=5.9.0`.

### 🎯 v3.0 Roadmap HOÀN TẤT
- ✅ Phase 1: User Management UI + Security (v1.8.0)
- ✅ Phase 2: Dashboard & Analytics Pro (v1.9.0)
- ✅ Phase 3: Dual Camera + PIP Mode (v1.10.0)
- ✅ Phase 4: System Health Dashboard (v2.0.0)

---

## [v1.10.0] - 2026-04-09 (Dual Camera + PIP Mode)

### 📹 Tính Năng Lớn
- **Dual Camera Side-by-Side:** Trạm có 2 camera → hiển thị song song 50/50. Toggle "1 Cam / Dual / PIP".
- **Picture-in-Picture (PIP):** Camera 1 chiếm full, Camera 2 small overlay góc dưới phải.
- **MediaMTX Dual Path:** Backend tự tạo path `station_{id}_cam2` cho camera phụ. Live view WebRTC riêng biệt.
- **Grid Badge:** Ô grid hiển thị badge "2 CAM" cho trạm có camera phụ.

### 🏗️ Kiến Trúc
- **`api.py`**: `CameraStreamManager` quản lý cam2_url riêng. `_mtx_add_path` hỗ trợ suffix. Endpoint `GET /api/live-cam2`.
- **`App.jsx`**: `cameraMode` state ('single-cam' | 'dual' | 'pip'). Conditional render iframe cho dual/PIP. Toggle 3 nút chỉ hiện khi hasCam2.

---

## [v1.9.0] - 2026-04-09 (Dashboard & Analytics Pro)

### 📊 Tính Năng Lớn
- **Dashboard Page:** Trang tổng quan với biểu đồ sản xuất, xu hướng, so sánh trạm. Toggle bằng nút BarChart3 ở header.
- **Biểu Đồ Sản Xuất Theo Giờ:** BarChart (Recharts) hiển thị số đơn theo từng giờ (0-23h). Filter theo ngày và trạm.
- **Xu Hướng 7 Ngày:** LineChart hiển thị trend sản xuất 7 ngày gần nhất.
- **So Sánh Trạm:** PieChart (donut) so sánh năng suất các trạm trong ngày.
- **Xuất CSV:** Download báo cáo danh sách đơn theo filter (ngày, trạm) dạng CSV.

### 🏗️ Kiến Trúc
- **`Dashboard.jsx`** (mới): Component dashboard với Recharts (BarChart, LineChart, PieChart).
- **`database.py`**: 4 hàm analytics mới (get_hourly_stats, get_daily_trend, get_stations_comparison, get_records_for_export).
- **`api.py`**: 4 endpoints mới (`GET /api/analytics/hourly`, `GET /api/analytics/trend`, `GET /api/analytics/stations-comparison`, `GET /api/export/csv`).
- **Recharts** (`npm install recharts`): Thư viện biểu đồ React (~160KB gzip).

---

## [v1.8.0] - 2026-04-09 (User Management UI + Security)

### 👤 Tính Năng Lớn
- **User Management Modal:** Giao diện quản lý user chuyên nghiệp với 3 tab (Người dùng, Phiên hoạt động, Nhật ký hệ thống). ADMIN tạo/sửa/khoá/xoá user trực tiếp từ UI.
- **Đổi Mật Khẩu:** Dropdown user → "Đổi mật khẩu". Xác thực mật khẩu cũ, validate độ dài, confirm match.
- **Audit Log:** Ghi lại mọi hành động quan trọng (LOGIN, LOGOUT, START_RECORD, STOP_RECORD, CREATE_USER, DELETE_USER, CHANGE_PASSWORD, FORCE_END_SESSION). Tự động dọn log cũ sau 90 ngày.
- **Session Management:** Xem tất cả phiên đang active (user, trạm, thời gian). ADMIN có thể force-kick session.

### 🏗️ Kiến Trúc
- **`database.py`**: Thêm bảng `audit_log`, 5 hàm mới (log_audit, get_audit_logs, get_active_sessions, get_session_by_id, end_session_by_id).
- **`api.py`**: 4 endpoints mới (`PUT /api/auth/change-password`, `GET /api/sessions/active`, `DELETE /api/sessions/{id}`, `GET /api/audit-logs`). Audit logging trên 10 action points.
- **`UserManagementModal.jsx`** (mới): 638 dòng, 3-tab UI với CRUD user, session viewer, audit log viewer.
- **`App.jsx`**: Users button (ADMIN-only), user dropdown với đổi mật khẩu, modal integration.

---

## [v1.7.0] - 2026-04-09 (Multi-Camera Live View UI)

### 🖥️ Tính Năng Lớn
- **Overview Grid Mode:** Hiển thị tất cả camera trạm đồng thời trong lưới responsive. Tự động tính số cột dựa trên số trạm (2x2, 3x2, v.v.). Click vào ô → zoom sang single view.
- **View Mode Toggle:** Nút chuyển đổi giữa Single View và Overview Grid ở header (chỉ hiện khi có ≥2 trạm).
- **Click-to-Zoom:** Click ô grid → chuyển sang single view cho trạm đó. Nút "Tổng quan" để quay lại grid.
- **Per-Station Status:** Theo dõi trạng thái ghi hình riêng cho từng trạm trong grid — badge RECORDING/PROCESSING/SẴN SÀNG trên mỗi ô.

### 🎨 UI/UX
- Grid responsive: mobile 1 cột, tablet 2 cột, desktop auto-fill.
- Hover effect trên grid tile: scale + border highlight.
- Barcode simulator ẩn trong grid mode (chỉ hiện ở single mode).
- Station selector ẩn trong grid mode.
- SSE subscribe tất cả trạm trong grid mode — realtime status update.

---

## [v1.6.0] - 2026-04-09 (User Management & Access Control)

### 🔐 Tính Năng Lớn
- **JWT Authentication:** Hệ thống đăng nhập bằng Username/Password với JWT token (PyJWT). Token hết hạn sau 8 giờ (1 ca làm việc), leeway 30s cho đồng hồ LAN không đồng bộ.
- **Role-Based Access Control (RBAC):** Hai vai trò ADMIN (toàn quyền) và OPERATOR (chỉ ghi đơn/xem lịch sử). Tự động ẩn/hiển các nút chức năng theo vai trò.
- **Session Locking:** Acquire/Heartbeat/Release session khi quét mã vạch. Ngăn nhiều người dùng cùng ghi trên 1 trạm. Session tự expire khi server khởi động lại.
- **User Management (ADMIN):** CRUD người dùng đầy đủ — tạo, sửa tên/vai trò/trạng thái, xoá. API được bảo vệ bởi `require_admin` dependency.
- **Auto-create Admin:** Lần đầu khởi động, tự động tạo tài khoản `admin` / mật khẩu `08012011`. Không cần setup thủ công.

### 🗑 Xóa Bỏ
- **PIN System hoàn toàn:** Xóa PinModal, `/api/verify-pin`, mã PIN ở SetupModal. Thay thế bằng user/password login.
- `PinModal.jsx` không còn được import (file vẫn tồn tại để tham khảo).

### 🎨 UI/UX
- **Login Form:** Giao diện đăng nhập glassmorphism với username/password, lỗi hiển thị inline. Conditional render — không dùng react-router.
- **User Info Header:** Hiển thị tên người dùng + vai trò + nút đăng xuất ở header.
- **Role-based UI:** Nút Cloud Sync, Settings, Add Station, Delete Record chỉ hiện cho ADMIN. OPERATOR chỉ thấy giao diện ghi đơn và xem lịch sử.
- **Auto-logout on 401:** Axios interceptor tự động đăng xuất khi token hết hạn hoặc không hợp lệ.

### 🏗️ Kiến Trúc
- **`auth.py`** (mới): JWT token creation/verification, bcrypt password hashing, `get_current_user()` và `require_admin()` FastAPI dependencies.
- **`database.py`**: Thêm bảng `users` (username, password_hash, role, full_name, is_active) và `sessions` (user_id, station_id, started_at, last_heartbeat, status). 13 hàm auth/session mới.
- **`api.py`**: Auth endpoints (login/me/logout), user CRUD (ADMIN only), session locking (acquire/heartbeat/release), RBAC protection trên TẤT CẢ endpoints.
- **`requirements.txt`**: Thêm `PyJWT>=2.8.0`, `passlib[bcrypt]>=1.7.4`.

### 🐛 Sửa Lỗi
- **OPERATOR 401 bug fix:** `checkSettings()` không còn gọi trên mount — chỉ gọi khi mở SetupModal (ADMIN-gated). Tránh OPERATOR bị logout do 401 từ `/api/settings` (ADMIN-only).

---

## [v1.5.0] - 2026-04-09 (Video Pipeline Reliability)

### 🚀 Tính Năng Lớn
- **100% Video Guarantee:** Đảm bảo mọi video ghi hình đều được tracking từ lúc bắt đầu. DB record tạo TRƯỚC khi FFmpeg start, không bao giờ mất dấu video dù server crash.
- **VideoWorker (Background Queue):** Tách luồng xử lý video ra khỏi barcode scanning. Operator quét STOP → trạm giải phóng ngay lập tức → VideoWorker xử lý convert/verify ở background. Operator không bao giờ bị block.
- **Pre-flight Checks:** Trước khi ghi, kiểm tra tự động: ổ cứng còn đủ ≥500MB, FFmpeg còn hoạt động, trạm không đang ghi/đang xử lý. Từ chối ghi nếu điều kiện không đủ.
- **Post-processing Verify:** Sau khi convert .ts→.mp4, dùng FFprobe verify file hợp lệ (duration > 0, codec valid). Video lỗi → mark FAILED + cảnh báo Telegram ngay lập tức.
- **Crash Recovery:** Khi server khởi động lại, tự động detect records bị treo (RECORDING/PROCESSING). Nếu file .ts còn → convert sang MP4. Nếu mất hoàn toàn → mark FAILED + cảnh báo Telegram.
- **SSE Realtime Updates:** Thay thế polling bằng Server-Sent Events. Frontend nhận push ngay khi status thay đổi (RECORDING → PROCESSING → READY/FAILED). Giảm ~1800 requests/giờ.

### 🎨 UI/UX
- **Status Badges:** Mỗi thẻ lịch sử hiển thị badge trạng thái: 🔴 RECORDING, 🟡 PROCESSING, 🟢 READY, ❌ FAILED.
- **Live View Overlay:** Badge "ĐANG XỬ LÝ VIDEO" (amber) hiển thị khi video đang convert.
- **Video Playback Guard:** Disable nút play cho video chưa xử lý xong (RECORDING/PROCESSING).

### 🏗️ Kiến Trúc
- **`video_worker.py`** (mới): ThreadPoolExecutor(max_workers=1), sequential processing, no race conditions.
- **`database.py`**: Thêm `status` column, `create_record()`, `update_record_status()`, `get_pending_records()`.
- **`recorder.py`**: Xóa fallback rename .ts→.mp4 (tránh tạo file invalid khi convert fail).
- **`api.py`**: SSE endpoint `/api/events`, pre-flight checks, crash recovery, handle_scan rewrite.

### 📋 Telegram Alerts
- File mất hoàn toàn → FAILED → cảnh báo Telegram ngay.
- Convert thất bại → FAILED → cảnh báo Telegram ngay.
- Recovery thất bại sau crash → cảnh báo Telegram ngay.
- Recovery thành công / server crash / recording dừng → không cảnh báo (không cần).

---

## [v1.4.0] - 2026-04-09 (WebRTC + Recording Overhaul)

### 🚀 Tính Năng Lớn
- **WebRTC Live View qua MediaMTX:** Thay thế toàn bộ MJPEG/OpenCV pipeline bằng MediaMTX + WebRTC. Live view giờ dùng sub-stream H.264 (640x352) remux trực tiếp qua MediaMTX → browser decode bằng hardware. Độ trễ gần như thời gian thực (~200ms), CPU server gần như 0.
- **MPEG-TS Safe Recording:** Ghi hình dưới dạng MPEG-TS (streamable, không corrupt khi mất điện/sập process). Khi dừng ghi, tự động convert sang MP4 với `-movflags +faststart`.
- **GPU Hardware Transcode:** Auto-detect GPU encoder (Intel QSV, NVIDIA NVENC, AMD AMF, Apple VideoToolbox) để transcode HEVC→H.264 khi lưu video. Fallback `libx264 ultrafast` nếu không có GPU.
- **Async Video Saving:** Quá trình lưu video chạy trên thread riêng, không block barcode scanning. Frontend hiển thị trạng thái "Đang lưu video..." và tự refresh khi xong.
- **Double-stop Protection:** `_stop_lock` + `_stopping_recorders` dict ngăn race condition khi nhiều scan request trigger concurrent `stop_recording()`.

### ✨ Cải Tiến
- **Video Player Pro rewrite:** Progress bar với seek, time display, volume, playback speed (0.5x-2x), keyboard shortcuts (Space, arrows, Esc), auto-hide controls, snapshot, download.
- **Frontend status badges:** Green (idle), red pulse (recording), amber pulse (saving).
- **`install_windows.bat` rewrite:** Auto-install Python 3.13.3 + Node.js v22 LTS + FFmpeg + MediaMTX, tạo firewall rule, desktop shortcut. Dùng `goto` labels thay vì nested `if/else`.
- **`start_windows.bat` rewrite:** Khởi động MediaMTX + Python server, mở Chrome Kiosk mode. Kill chính xác process (port-based), không kill tất cả python.exe.
- **`start.sh` update (macOS):** Khởi động MediaMTX + FFmpeg PATH + proper cleanup.
- **`.gitignore` update:** Thêm `bin/`, `hls/`, `install_log.txt`.

### 🗑 Xóa Bỏ
- Loại bỏ dependency OpenCV (`cv2`) khỏi backend — live view không còn dùng OpenCV.
- Loại bỏ MJPEG multipart streaming pipeline.
- Loại bỏ FLV.js, HLS.js (đã thử và không phù hợp bằng WebRTC).

### 📋 Yêu cầu mới
- **MediaMTX** (`bin/mediamtx/mediamtx.exe`): Media server proxy RTSP→WebRTC. Tự động download bởi `install_windows.bat`.

---

## [v1.3.2] - 2026-04-08 (macOS + Windows Fix)

### 🚀 Tính Năng Mới
- **macOS 1-click installer**: Double-click `Install V-Pack Monitor.command` → tự động cài tất cả. Double-click `Start V-Pack Monitor.command` → khởi động server + mở trình duyệt.
- **`install_macos.sh`**: Script cài đặt tự động qua Terminal — check Python 3.10+, Node.js, tạo venv, pip install, build frontend.

### ✨ Cải Tiến
- **Dockerfile**: Python 3.10 → 3.14 (tương thích `str | None` syntax).
- **README.md**: Version v1.3.2, thêm hướng dẫn macOS + Docker, fix lệnh `python api.py` → `uvicorn`.
- **README_SETUP.md**: Version v1.3.2, thêm hướng dẫn macOS + Docker + MAC Address.

### 🐛 Sửa Lỗi
- **Windows install_windows.bat**: Cửa sổ chớp tắt khi `python` không trong PATH — thêm fallback sang `py` launcher, error handling + `pause` ở mọi nhánh lỗi.
- **Windows start_windows.bat**: Thêm check venv tồn tại trước khi activate, thông báo lỗi rõ ràng nếu chưa cài đặt.

---

## [v1.3.1] - 2026-04-08 (Auto-Discovery Update)

### 🚀 Tính Năng Mới
- **Tự Động Tìm Lại Camera (Auto-Discovery by MAC)**: Khi camera đổi IP do sự cố mạng/DHCP reset, hệ thống tự động quét LAN theo MAC Address, cập nhật IP mới và reconnect — không cần can thiệp tay.
- **Nút "Quét IP" trong Cài Đặt**: Nhập MAC Address (in trên tem đáy camera) → bấm quét → tìm ngay IP mới.
- **Badge trạng thái reconnect**: Hiển thị "Đang tìm lại Camera..." / "Đã tìm thấy IP mới" trên camera preview.
- **Công cụ test RTSP** (`test_rtsp.py`): Script kiểm tra nhanh kết nối RTSP camera theo IP + Safety Code, hỗ trợ tất cả brand.

### ✨ Cải Tiến
- Upgrade Python runtime từ 3.9 → **3.14** (hiệu năng, bảo mật).
- Sửa lỗi phát hiện subnet LAN (`192.168.5.x` thay vì fallback sai `192.168.1.x`).
- Sửa lỗi parse MAC Address có octet thiếu số 0 (VD: `30:24:50:48:9:38`).
- Tắt OpenCV warning spam khi camera offline.
- `start.sh` cleanup: `kill -9` + signal trap, `source venv/bin/activate`.
- Thêm `pyTelegramBotAPI` vào `requirements.txt`.

---

## [v1.3.0] - 2026-04-08 (Premium Release)

Gói nâng cấp "Premium Features" tập trung nâng cao khả năng quản trị, phòng ngừa rủi ro và tăng cường tốc độ xử lý khiếu nại cho nhân viên đóng hàng.

### 🚀 Những Thay Đổi Lớn (Major Features)
- **Cảnh Báo Ổ Cứng Hết Chỗ (Disk Health Alerts)**: Hệ thống làm mới tự động quét dữ liệu thư mục ghi hình. Thanh Progress bar chuyển đỏ và nháy liên tục khi cảnh báo dung lượng thực tế trống dưới 10%, nhằm ngăn ngừa lỗi không thể ghi đè Video.
- **Tích hợp Chatbot Telegram Trực Tiếp (Two-way Comms)**: Cấu hình linh hoạt qua UI Modal (Token, Chat ID). Phân luồng Cảnh báo "Lỗi đứt gãy Cloud Sync" tự động văng vào máy chủ. Hỗ trợ lệnh Listen Control trên Mobile Chat: gọi `/baocao` báo cáo năng suất ngày, gọi `/kiemtra` hiển thị danh sách thiết bị.
- **Nâng Cấp Video Player Pro**: Trình xem lại vận đơn nhúng gọn gàng trong Modal (Pop-up), loại bỏ sự phiền phức mở Tab mới. Trang bị tốc độ tua nhanh 2.0x, và chế tạo công cụ "Chụp Hình - Snapshot", xuất khẩu bằng chứng khung hình thành JPG lưu nhanh chóng.

### ✨ Cải Tiến (Improvements)
- Hỗ trợ đầy đủ luồng Camera RTPS đến từ các thiết bị `Tenda`, `TP-Link Tapo`, `EzViz`, song hành với `Imou` và `Dahua` truyền thống.
- **Production Build All-in-one**: Hỗ trợ xuất xưởng (Export) trực tiếp toàn bộ Backend + UI thành một file nhị phân duy nhất `.exe`/`.app` cực gọn với `PyInstaller` và Script kịch bản cài đặt `inno_setup`. Cạy mở sự hiện diện "như một phần mềm thực sự", không cần lệnh mở cmd.

### 🧹 Code Hygiene (Dọn dẹp mã nguồn)
- Chuẩn hoá toàn bộ Linter rules PEP8 (chặn Warning) qua các file lõi SQL và Backend.
- Tối ưu luồng tiến trình (Daemon thread) để nhốt trình lắng nghe Telegram an toàn song song cạnh Event Loop WebSocket FastAPI.
- Xóa bỏ rác Code và các comment lỗi thời.

---

## [v1.2.0] - 2026-04-05 (Cloud Sync Update)
- Bổ sung luồng kết nối Google Drive & S3.
- ...

## [v1.1.0] - Giao Diện Barcode Scanner UI
- Ra mắt công cụ quét mã vạch chuyên dụng và Trạm thu thập Multi-Station, phân chia logic xử lý nhiều Camera.

## [v1.0.0] - Bản Nguyên Góc
- MVP API Video MP4 bằng OpenCV. Hỗ trợ 1 Camera duy nhất.
