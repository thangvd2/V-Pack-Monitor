# Design Patterns & Best Practices — V-Pack Monitor v3.4.0

> Audit date: 2026-04-24 | 75 patterns identified across backend, frontend, testing, and infrastructure.

---

## Backend Architecture (27 patterns)

### 1. Repository Pattern
**File:** `database.py` (entire file)

All SQLite operations encapsulated behind module-level functions. Routes never write raw SQL — they call `database.create_record()`, `database.get_records_v2()`, etc. Each function opens its own connection via `get_connection()`, performs the operation, and commits.

### 2. Module Registry Pattern
**File:** `routes_*.py` → `api.py:687-690`

Each route module exports `register_routes(app)`. Api.py calls each in sequence:

```python
routes_auth.register_routes(app)
routes_stations.register_routes(app)
routes_records.register_routes(app)
routes_system.register_routes(app)
```

Keeps `api.py` clean (0 route definitions, only app factory + shared state).

### 3. Singleton Pattern (Module-Level Shared State)
**File:** `api.py:68-98`

Python modules are singletons by default. All mutable shared state declared at module scope:

```python
active_recorders = {}       # L68
active_waybills = {}        # L69
active_record_ids = {}      # L70
_processing_count = {}      # L71
stream_managers = {}        # L74
reconnect_status = {}       # L76
_sse_clients = []           # L97
```

### 4. Per-Concern Locking (Lock Striping)
**File:** `api.py:72-88`

8 locks for different domains. Maximizes concurrency — scanning Station 1 doesn't block SSE broadcasts or Station 2:

| Lock | Guards |
|------|--------|
| `_processing_lock` | `_processing_count` |
| `_recording_timers_lock` | `_recording_timers`, `_recording_start_times` |
| `_recorders_lock` | `active_recorders`, `active_waybills`, `active_record_ids` |
| `_streams_lock` | `stream_managers`, `reconnect_status` |
| `_station_locks_lock` | `_station_locks` dict itself |
| `_cache_lock` | `_update_check_cache` |
| `_login_attempts_lock` | `_login_attempts` |
| `_sse_lock` | `_sse_clients` |

Plus **per-station locks**: `_station_locks = {}` — dynamic locks per station to prevent double-scan race conditions.

### 5. Observer / Pub-Sub Pattern (SSE Event Broadcasting)
**File:** `api.py:101-111` (publisher), `routes_records.py:443-484` (endpoint)

Classic fan-out pub-sub. `notify_sse()` pushes to all subscriber queues:

```python
def notify_sse(event_type, data):
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with _sse_lock:
        for i, q in enumerate(_sse_clients):
            q.put_nowait(msg)
```

Event types: `video_status`, `station_status`, `update_progress`, `recording_warning`. Dead subscribers auto-pruned.

### 6. Strategy Pattern — Hardware Encoder Selection
**File:** `recorder.py:39-74`

Runtime probe in priority order: `h264_qsv` → `h264_nvenc` → `h264_amf` → `h264_videotoolbox` → fallback `libx264`. Result cached in `_hw_encoder_cache`.

### 7. Strategy Pattern — Camera Brand RTSP URLs
**File:** `api.py:304-328`

Each camera brand (imou/dahua, tenda, ezviz, tapo) has different RTSP URL format. Branch on `brand` parameter.

### 8. Strategy Pattern — Cloud Provider Selection
**File:** `cloud_sync.py:167-218`

`CLOUD_PROVIDER` setting selects between `GDRIVE` and `S3`. Each provider has its own upload function.

### 9. Builder Pattern — FFmpeg Command Construction
**File:** `recorder.py:77-331`

Incremental command assembly:

1. Base: `["ffmpeg", "-y"]`
2. Hardware acceleration flags (conditional)
3. Input: `["-i", input_file]`
4. Encoder-specific args via `_build_pip_encode_args()`
5. Output: `["-movflags", "+faststart", output_file]`

PIP mode (L265-331) is the most complex builder with `filter_complex`, dual inputs, and encoder-specific args.

### 10. Template Method Pattern — Recording Modes
**File:** `recorder.py:171-338`

`start_recording()` defines invariant skeleton (sanitize waybill, generate filename, log results). Variant steps branch on mode: SINGLE (L190), DUAL_FILE (L216), PIP (L265).

### 11. Queue/Worker Pattern (Bounded)
**File:** `video_worker.py:25, 158-181`

`ThreadPoolExecutor(max_workers=1)` serializes video processing. `_MAX_PENDING=10` backpressure — rejects submissions when overloaded. Callers check return value and mark records as FAILED.

### 12. Lifespan / Context Manager Pattern
**File:** `api.py:538-636`

Standard FastAPI async context manager:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # STARTUP: init_db(), recover_pending(), CameraStreamManager.start(), telegram_bot.start()
    yield
    # SHUTDOWN: cancel timers, stop managers, stop recorders, video_worker.shutdown(), telegram_bot.stop()
```

### 13. Connection Manager Pattern
**File:** `database.py:136-158`

`get_connection()` returns configured SQLite connection with consistent pragmas:

```python
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA busy_timeout = 5000")
    conn.row_factory = sqlite3.Row
    return conn
```

### 14. Migration Pattern — Encryption Upgrade
**File:** `database.py:59-123`

Two-phase crypto migration:
- `_decrypt_value()` handles both `enc:v1:` (XOR) and `enc:v2:` (Fernet) — read compatibility
- `_migrate_v1_to_v2()` runs on startup, re-encrypts all v1 values with Fernet
- `_encrypt_value()` always writes v2 format

### 15. Dependency Injection (FastAPI Depends)
**File:** `auth.py:76-114`

Reusable type aliases combining annotation + DI:

```python
CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_admin)]
```

Routes declare `current_user: CurrentUser` — zero boilerplate auth.

### 16. Chain of Responsibility — Barcode Scan Dispatch
**File:** `routes_records.py:300-335`

Sequential handler chain: EXIT → STOP → already_recording → START. Each handler either processes the request or falls through.

### 17. Crash Recovery Pattern
**File:** `api.py:466-535`

`_recover_pending_records()` runs in daemon thread on startup:
1. Find records with status RECORDING or PROCESSING
2. Check for `.tmp.ts` files, attempt transcode/remux
3. Validate with ffprobe
4. Mark READY or FAILED, send Telegram alerts for unrecoverable records

### 18. Adapter Pattern — MediaMTX API Wrapper
**File:** `api.py:114-172`

`_mtx_add_path()` / `_mtx_remove_path()` adapt MediaMTX REST API into simple Python functions with retry logic and fallback (replace → delete+add).

### 19. Self-Healing Monitor Pattern
**File:** `api.py:175-302`

`CameraStreamManager._monitor_loop`:
- Checks MediaMTX path health every 15s
- Re-registers broken paths
- Detects broken cam2 feeds, removes them
- `_try_rediscover_camera()` scans LAN by MAC when camera goes offline, updates DB and reconnects

### 20. Graceful Degradation — FTS5 → LIKE Fallback
**File:** `database.py:589-682`

Search queries attempt FTS5 trigram match first. If `MATCH` fails (special chars, FTS5 missing, query < 3 chars), catches `OperationalError` and falls back to `LIKE`.

### 21. Lazy Initialization
**Files:** `video_worker.py:168-170`, `database.py:277,1004,1041`, `cloud_sync.py:52`

`ThreadPoolExecutor`, `bcrypt`, `Fernet`, `google.oauth2` — created/imported only on first use. Avoids startup cost for optional features.

### 22. Cache with TTL
**Files:** `recorder.py:36`, `telegram_bot.py:23-41`, `routes_system.py:43-44`, `cloud_sync.py:40-58`

| What | TTL | Location |
|------|-----|----------|
| HW encoder detection | Permanent | `recorder.py:36` |
| Bot token | 5 minutes | `telegram_bot.py:25` |
| GitHub update check | 1 hour | `routes_system.py:44` |
| Google Drive creds | Until file modified (mtime) | `cloud_sync.py:40-58` |

### 23. Guard / Mutex Pattern (Single-Execution)
**Files:** `cloud_sync.py:61`, `routes_system.py:41-42`, `database.py:131`

- `_sync_lock` prevents concurrent cloud syncs
- `_update_lock` + `_is_updating` flag prevents concurrent system updates
- `_init_lock` prevents concurrent DB initialization

### 24. Exponential Backoff
**File:** `telegram_bot.py:96-105`

Classic pattern with 60s cap: 3s → 6s → 12s → 24s → 48s → 60s. Resets to 3s on success.

### 25. Parallel Execution Pattern (LAN Ping Sweep)
**File:** `network.py:157-163`

```python
with ThreadPoolExecutor(max_workers=50) as executor:
    futures = {executor.submit(_ping_host, f"{prefix}.{i}"): i for i in range(1, 255)}
    for future in as_completed(futures, timeout=17):
        ...
```

254 hosts in parallel with 50 threads, 17s timeout.

### 26. Path Traversal Defense
**Files:** `routes_records.py:272-275`, `recorder.py:173-178`, `routes_system.py:270-276`

- Waybill code sanitization (strip special chars)
- Download path validation (prevent `../` traversal)
- Zip Slip prevention (validate extracted paths stay within target dir)
- SQL column whitelist (`database.py:869-870`)

### 27. Middleware Pattern
**File:** `api.py:542-553, 658-664`

- CORS middleware with restricted methods
- Custom async exception handler (suppress connection reset errors in SSE)

---

## Frontend Architecture (28 patterns)

### 28. Container / Presentational Component
**File:** `App.jsx` (container) vs children (presentational)

App.jsx holds ALL application state (~60 `useState` hooks). Children receive data and callbacks via props. Pure presentational components: `AdminDashboard`, `MtxFallback`. Semi-container: `Dashboard`, `SystemHealth` (fetch own chart/health data).

### 29. Observer Pattern — SSE / EventSource
**File:** `App.jsx:385-523`

Typed event listeners on EventSource:
- `video_status` → update station statuses, packing status, play sounds, refresh records
- `update_progress` → show system update progress
- `recording_warning` → show toast + play warning sound

Two modes: global SSE (admin/operator grid) vs station-specific SSE (operator single view).

### 30. Ref Synchronization (Stale Closure Prevention)
**File:** `App.jsx:264-292`

11 refs synced via useEffect, read inside SSE callbacks and event handlers:

| Ref | Purpose |
|-----|---------|
| `packingStatusRef` | Packing state in barcode handler |
| `searchTermRef` | Search term in fetchRecords |
| `recordsPageRef` | Current page in fetchRecords |
| `dateFromRef` | Date filter in fetchRecords |
| `dateToRef` | Date filter in fetchRecords |
| `statusFilterRef` | Status filter in fetchRecords |
| `stationsRef` | Stations array in SSE handler |
| `activeRecordIdRef` | Current recording ID |
| `abortControllerRef` | Fetch cancellation |
| `toastTimeoutRef` | Toast cleanup |
| `barcodeSimInputRef` | Direct DOM access |

### 31. Role-Based Access Control (RBAC)
**File:** `App.jsx` (23+ guard locations), `Dashboard.jsx`, `SystemHealth.jsx`

- `requestAdminAccess()` gateway with password re-confirmation
- Conditional rendering: admin sees grid view, tab navigation, all stations, delete records, settings
- Operator sees: assigned station only, barcode simulator, limited controls
- `viewMode` auto-set to `'grid'` for admin on login

### 32. State Machine (Recording Flow)
**File:** `App.jsx`

```
idle → packing  (scan START response / SSE RECORDING event)
packing → idle  (SSE PROCESSING/READY/FAILED/DELETED)
packing → idle  (scan error response)
```

Ref-based guard: `packingStatusRef.current` checked in barcode handler to prevent double-scan.

### 33. AbortController Pattern (Cancellable Fetches)
**File:** `App.jsx:279, 667-684`

Cancel previous fetch when filter changes:

```javascript
if (abortControllerRef.current) abortControllerRef.current.abort();
abortControllerRef.current = new AbortController();
// ... fetch with signal, detect axios.isCancel in catch
```

### 34. Error Boundary
**File:** `App.jsx:179-202`

Class component wraps entire App. Catches React render errors, shows fallback UI.

### 35. Guard / Protected Route Pattern
**File:** `App.jsx:1015-1112`

Three sequential gates as early returns:
1. Auth loading spinner (token restore in progress)
2. Login form (no currentUser)
3. Station selection (OPERATOR without station)

Plus: must-change-password enforcement, 401 interceptor auto-logout.

### 36. Tab / Strategy UI
**Files:** `App.jsx:227`, `Dashboard.jsx:94`, `UserManagementModal.jsx:55`

| Component | State | Tabs |
|-----------|-------|------|
| App.jsx | `adminTab` | Vận hành / Tổng quan |
| Dashboard | `dashTab` | Analytics / Health |
| UserManagementModal | `activeTab` | Users / Sessions / Logs |

### 37. Lift State Up
**File:** `App.jsx` (55+ useState)

ALL significant state lives in App.jsx. No child manages shared state. Everything flows via props.

### 38. Fallback / Graceful Degradation
**Files:** `MtxFallback.jsx`, `App.jsx`, `SystemHealth.jsx`

- MediaMTX down → `MtxFallback` (shows instructions instead of blank)
- SystemHealth fetch error → retry button
- ErrorBoundary catches render crashes

### 39. Modal Pattern
**Files:** `VideoPlayerModal.jsx`, `SetupModal.jsx`, `UserManagementModal.jsx`

Shared structure: `if (!isOpen) return null` → backdrop click = close → `stopPropagation` on inner content. Parent controls open/close via state.

### 40. Form Validation (Touched-State Pattern)
**File:** `SetupModal.jsx:125-206`

- `touched` state tracks which fields user interacted with
- `validate()` returns array of error codes
- `fieldBorder()` renders color based on touched + error state
- Server-side conflict check with debounce (300ms)
- IP/MAC validators: `isValidIPv4`, `isValidIPv6`, `isValidMAC`

### 41. CRUD Pattern
**File:** `UserManagementModal.jsx`

Full CRUD for users: Create (with validation) → Read (fetch on mount) → Update (inline editing) → Delete (with self-delete guard) → Toggle active → Reset password.

### 42. Debouncing / Throttling
**Files:** `App.jsx`, `SetupModal.jsx`, `VideoPlayerModal.jsx`

| What | Delay | Location |
|------|-------|----------|
| Search input | 300ms | `App.jsx:49, 675` |
| Barcode buffer | 100ms | `App.jsx:46, 954` |
| Conflict check | 300ms | `SetupModal.jsx:157` |
| Video controls auto-hide | 3000ms | `VideoPlayerModal.jsx:59` |

### 43. Polling Pattern
**Files:** `App.jsx`, `SystemHealth.jsx`, `UserManagementModal.jsx`

| What | Interval | Location |
|------|----------|----------|
| Station status | 10s | `App.jsx:63` |
| Session heartbeat | 30s | `App.jsx:353` |
| Reconnect status | 10s | `App.jsx:609` |
| System health | 5s | `SystemHealth.jsx:72` |
| Sessions/logs auto-refresh | 30s | `UserManagementModal.jsx:132` |

### 44. Axios Interceptor Pattern
**File:** `App.jsx:364-377`

401 response → auto-logout. Global timeout + Authorization header set on login.

### 45. Rate Limiting / Cooldown
**File:** `notificationSounds.js:9-16`

600ms cooldown per sound type. `_lastPlayed` dict tracks last play time. Prevents duplicate rapid triggers.

### 46. Confirmation Dialog Pattern
**Files:** `App.jsx:296-298, 2204-2228`, `SetupModal.jsx:867-891`

Reusable confirm dialog with `showConfirmDialog(message, onConfirm)` callback. Used for delete records, delete station, unsaved changes, conflict warnings.

### 47. Component Composition
**File:** `Dashboard.jsx:50-84`

`StatCard` and `ChartCard` sub-components. Dashboard conditionally embeds `SystemHealth`. AdminDashboard composes `MtxFallback`.

### 48. Memoization (useMemo / useCallback)
**Files:** 15+ locations across all components

- `stationsIdStr` memoized from stations array (`App.jsx:379`)
- `activeStation` memoized lookup (`App.jsx:972`)
- `showToast`, `showConfirmDialog`, `doChangePassword` in useCallback
- `fetchHourly`, `fetchTrend`, `fetchStationsComparison` in Dashboard
- `fetchData` in SystemHealth

### 49. Cleanup Pattern (useEffect return)
**Files:** 13 useEffect cleanups across all components

| Effect | Cleanup |
|--------|---------|
| SSE EventSource | `es.close()` |
| Station status polling | `clearInterval` |
| Heartbeat interval | `clearInterval` |
| Reconnect polling | `clearInterval` + `active` flag |
| Search debounce | `clearTimeout` + `abort()` |
| Barcode scanner | `removeEventListener` + `clearTimeout` |
| Axios interceptor | `eject(interceptor)` |
| Video keyboard handler | `removeEventListener` |
| Video hide timer | `clearTimeout` |
| Health polling | `clearInterval` |
| Auto-refresh | `clearInterval` |
| Escape handler | `removeEventListener` |
| MTX status check | `active = false` flag |

### 50. Named Constants
**Files:** 6 files

```javascript
STATION_POLL_INTERVAL = 10000    // App.jsx:45
BARCODE_TIMEOUT = 100            // App.jsx:46
HEARTBEAT_INTERVAL = 30000       // App.jsx:47
SEARCH_DEBOUNCE = 300            // App.jsx:49
CHART_COLORS = [...]             // Dashboard.jsx:38
STATUS_CONFIG = {...}            // SystemHealth.jsx:12
ACTION_LABELS = {...}            // UserManagementModal.jsx:29
COOLDOWN_MS = 600                // notificationSounds.js:9
```

### 51. Promise.allSettled for Parallel Fetches
**File:** `SystemHealth.jsx:54-58`

Fetches health + processes + network in parallel. Each result checked independently (`status === 'fulfilled'`).

### 52. Race Guard (active flag)
**File:** `App.jsx:337, 585`

`let active = true` pattern prevents state updates after component unmount. Checked before `setState` calls.

### 53. Content-Disposition Parsing
**File:** `VideoPlayerModal.jsx:288-293`

Regex extraction of filename from download headers. Handles both `filename=` and `filename*=UTF-8''` formats. Falls back to `{waybillCode}.mp4`.

### 54. Singleton (IIFE / Lazy)
**Files:** `config.js`, `notificationSounds.js`

- `config.js` IIFE determines API_BASE at module load time
- `notificationSounds.js` lazy `AudioContext` creation on first user gesture

### 55. Multi-axis Conditional Rendering
**File:** `App.jsx:1609-2201`

5-axis rendering matrix: `viewMode` × `role` × `adminTab` × `cameraMode` × `showDashboard`.

---

## Testing & CI/CD (20 patterns)

### 56. Shared Fixtures (conftest.py)
**File:** `tests/conftest.py`

Layered fixture chain:

```
isolate_db → admin_user_id → admin_token → admin_headers
isolate_db → operator_user_id → operator_token → operator_headers
isolate_db + client (monkeypatches api shared state + patches CameraStreamManager)
```

### 57. Test Isolation (tmp_path + Fresh DB Per Test)
**File:** `tests/conftest.py:28-34`

`isolate_db` fixture redirects `database.DB_FILE` to `tmp_path/test.db`, resets ALL shared mutable state to empty dicts. `database.py:131-133` ensures re-init when DB path changes.

### 58. Mock / Stub Pattern
**Files:** `test_recorder.py`, `test_video_worker.py`, `test_auto_stop_timer.py`, `test_cloud_sync.py`, `test_telegram.py`

- `subprocess.Popen` / `subprocess.run` for FFmpeg mocking
- `sys.modules.setdefault(_mod, MagicMock())` for heavy deps (telebot, psutil)
- `patch.object(api, "notify_sse")` captures SSE events for assertion
- `patch("requests.post")` for Telegram API

### 59. Spy Pattern
**File:** `test_auto_stop_timer.py:86-89`

`MagicMock(wraps=timer.cancel)` — verifies timer cancellation without preventing actual behavior.

### 60. Parameterized by Enumeration
**File:** `test_api_helpers.py`

22 test methods covering all camera brands × channels × edge cases. Loop-based parameterization in `test_database_edge_cases.py:182-193` for SQL injection / unicode / spaces.

### 61. Test Organization by Concern
**Files:** 14 test files

| File | Concern | Classes |
|------|---------|---------|
| `test_database.py` | DB layer | Encryption, Settings, Records, Stations, Users, Sessions, Audit, Analytics |
| `test_database_edge_cases.py` | Boundary/security | SQL Injection, Boundary, Input Limits |
| `test_auth.py` | Auth | JWT, Token Revocation, RBAC |
| `test_api_routes.py` | API integration | Login, CRUD, Download, Export, Live Preview |
| `test_api_hardening.py` | Input validation | Station Validation, Settings, Auto-Update, RBAC Edge Cases |
| `test_security_regression.py` | Security | 18 tests covering 26 vulnerabilities |
| `test_video_worker.py` | Worker + recovery | Worker lifecycle, crash recovery |
| `test_recorder.py` | FFmpeg | HW encoder, SINGLE/DUAL/PIP modes |
| `test_video_search.py` | Search/pagination | FTS5, Trigram, Pagination, Date/Status Filter, Sort |
| `test_auto_stop_timer.py` | Timer lifecycle | 13 tests for timer create/cancel/fire |
| `test_network.py` | Network | MAC validation, ARP scan, LAN discovery |
| `test_cloud_sync.py` | Cloud backup | S3, GDrive upload |
| `test_telegram.py` | Telegram | Send message |
| `test_api_helpers.py` | RTSP URLs | All brands × channels |

### 62. CI Pipeline with Gates
**File:** `.github/workflows/ci.yml`

```
changes (detect changed files)
  ├──→ python-test (pytest)
  ├──→ python-lint (ruff check)
  ├──→ frontend-build (npm ci → lint → build)
  ├──→ docs-only-bypass (skip all)
  ├──→ ai-sync-check (always)
  └──→ version-consistency (always)
release-check (if PR dev→master)
```

### 63. Path-Based CI Skip
**File:** `.github/workflows/ci.yml:21-37`

`dorny/paths-filter` detects python/frontend/docs-only groups. Docs-only changes skip all gates.

### 64. Dependency Caching
**File:** `.github/workflows/ci.yml:92-97, 119-121`

- Pip: `v1-${{ runner.os }}-pip-${{ hashFiles('requirements*.txt') }}`
- npm: `cache: "npm"` with `package-lock.json`

### 65. Pre-commit Hook Chain
**File:** `.pre-commit-config.yaml`

5 stages: Ruff lint+format → detect-secrets → ai-sync enforcement → branch protection → pytest+eslint+prettier.

### 66. Version Consistency CI
**File:** `scripts/check_version_consistency.py`

Cross-checks VERSION vs api.py header vs package.json vs README.md. Fails CI on mismatch.

### 67. Auto Version Bump
**File:** `scripts/bump_version.py`

Updates all 4 version locations atomically.

### 68. Branch Protection Hook
**File:** `.git-hooks/check-protected-branch.py`

Pre-push: blocks pushes to `master` and `dev`.

### 69. Docker Multi-Arch
**File:** `Dockerfile`

Runtime arch detection for MediaMTX download. Dual-process CMD: `mediamtx & python -m uvicorn api:app`.

### 70. PyInstaller Packaging
**Files:** `build.py`, `V-Pack-Monitor.spec`

3-step: `npm run build` → install PyInstaller → bundle backend + frontend dist into single executable. Runtime detection: `getattr(sys, 'frozen', False)`.

### 71. Monorepo Organization
**Project root**

Backend (Python/FastAPI) + frontend (React/Vite) + Docker + CI + scripts in one repo. Build script orchestrates both.

### 72. Auto-stop Timer State Machine
**File:** `api.py:78-81, 334-409`

Warning timer (540s) → SSE `recording_warning` event. Stop timer (600s) → auto-stop recording. Critical safety check at L353: `if current_record_id == record_id` prevents stopping wrong recording.

### 73. Secret Management (Encryption at Rest)
**File:** `database.py:27-56`

Fernet encryption for sensitive settings (bot token, cloud credentials). Key derived from JWT secret. `_SENSITIVE_KEYS` whitelist determines which settings to encrypt.

### 74. JWT + Token Revocation
**File:** `auth.py`

Access tokens (15min) + Refresh tokens (7days). Revocation list stored in DB. `get_current_user()` checks revocation on every request.

### 75. Feature Flags / Configuration-Driven Behavior
**Files:** `database.py`, `api.py`, `routes_system.py`

- `_VALID_RECORD_STATUSES` whitelist (`database.py:476`)
- `_VALID_ROLES` whitelist (`database.py:993`)
- `LIVE_VIEW_STREAM` setting: main vs sub stream (`api.py:559`)
- `RECORD_KEEP_DAYS` validated enum: 0/3/7/15/30/60/90/150/365 (`routes_system.py:414`)
- `_MAX_RECORDING_SECONDS = 600` hard cap (`api.py:42`)

---

## Architectural Observations

### Strengths
- **Clean separation**: `api.py` (0 routes) → `routes_*.py` → `database.py` → `auth.py`
- **Thread safety**: 8 per-concern locks + per-station locks + bounded worker queue
- **Crash resilience**: MPEG-TS format (streamable), crash recovery on startup, self-healing camera monitor
- **Test coverage**: 326 tests across 14 files with full isolation
- **Security**: Fernet encryption, JWT with revocation, path traversal defense, RBAC

### Opportunities
- **Custom hooks**: App.jsx at 2200+ lines — extraction candidates: `useSSE()`, `useAuth()`, `useToast()`, `useDebouncedFetch()`
- **Parameterized tests**: Use `@pytest.mark.parametrize` instead of test method enumeration
- **Error boundaries**: Only wraps App root — individual risky sections (SSE handler, video player) lack local boundaries
