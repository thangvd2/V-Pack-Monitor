# Design Patterns — V-Pack Monitor v3.4.0

> Audit date: 2026-04-24 | 36 patterns identified.
> Related: [BEST_PRACTICES.md](./BEST_PRACTICES.md) for coding conventions and standard techniques.

---

## Backend Architecture (20 patterns)

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

### 3. Singleton Pattern (Module-Level State + IIFE)
**Files:** `api.py:68-98`, `config.js`, `notificationSounds.js`

Python modules are singletons by default — all mutable shared state declared at module scope:

```python
active_recorders = {}       # api.py:68
active_waybills = {}        # api.py:69
active_record_ids = {}      # api.py:70
_processing_count = {}      # api.py:71
stream_managers = {}        # api.py:74
_sse_clients = []           # api.py:97
```

Frontend: `config.js` IIFE determines API_BASE at module load. `notificationSounds.js` lazy AudioContext singleton on first user gesture.

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

### 5. Observer / Pub-Sub Pattern (SSE)
**Files:** `api.py:101-111` (publisher), `routes_records.py:443-484` (endpoint), `App.jsx:385-523` (frontend subscriber)

Classic fan-out pub-sub. `notify_sse()` pushes to all subscriber queues:

```python
def notify_sse(event_type, data):
    msg = f"event: {event_type}\ndata: {json.dumps(data)}\n\n"
    with _sse_lock:
        for i, q in enumerate(_sse_clients):
            q.put_nowait(msg)
```

Frontend subscribes via `EventSource` with typed listeners: `video_status`, `update_progress`, `recording_warning`. Two modes: global SSE (admin grid) vs station-specific SSE (operator single view).

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
**Files:** `api.py:538-636` (app lifespan), `database.py:136-158` (connection manager)

App lifecycle managed via `@asynccontextmanager` — startup (init DB, MediaMTX, recover pending) + shutdown (cleanup). Database connection manager `get_connection()` ensures consistent pragmas (foreign_keys=ON, WAL, busy_timeout) on every connection.

### 13. Migration Pattern — Encryption Upgrade
**File:** `database.py:59-123`

Two-phase crypto migration:
- `_decrypt_value()` handles both `enc:v1:` (XOR) and `enc:v2:` (Fernet) — read compatibility
- `_migrate_v1_to_v2()` runs on startup, re-encrypts all v1 values with Fernet
- `_encrypt_value()` always writes v2 format

### 14. Dependency Injection (FastAPI Depends)
**File:** `auth.py:76-114`

Reusable type aliases combining annotation + DI:

```python
CurrentUser = Annotated[dict, Depends(get_current_user)]
AdminUser = Annotated[dict, Depends(require_admin)]
```

Routes declare `current_user: CurrentUser` — zero boilerplate auth.

### 15. Chain of Responsibility — Barcode Scan Dispatch
**File:** `routes_records.py:300-335`

Sequential handler chain: EXIT → STOP → already_recording → START. Each handler either processes the request or falls through.

### 16. Crash Recovery Pattern
**File:** `api.py:466-535`

`_recover_pending_records()` runs in daemon thread on startup:
1. Find records with status RECORDING or PROCESSING
2. Check for `.tmp.ts` files, attempt transcode/remux
3. Validate with ffprobe
4. Mark READY or FAILED, send Telegram alerts for unrecoverable records

### 17. Adapter Pattern — MediaMTX API Wrapper
**File:** `api.py:114-172`

`_mtx_add_path()` / `_mtx_remove_path()` adapt MediaMTX REST API into simple Python functions with retry logic and fallback (replace → delete+add).

### 18. Self-Healing Monitor Pattern
**File:** `api.py:175-302`

`CameraStreamManager._monitor_loop`:
- Checks MediaMTX path health every 15s
- Re-registers broken paths
- Detects broken cam2 feeds, removes them
- `_try_rediscover_camera()` scans LAN by MAC when camera goes offline, updates DB and reconnects

### 19. Graceful Degradation
**Files:** `database.py:589-682` (FTS5 → LIKE fallback), `MtxFallback.jsx` (MediaMTX down), `SystemHealth.jsx` (fetch error → retry), `App.jsx:179-202` (ErrorBoundary)

Multiple degradation layers:
- Backend: FTS5 trigram MATCH fails → catches `OperationalError` → falls back to LIKE
- Frontend: MediaMTX down → `MtxFallback` component (instructions instead of blank)
- Frontend: SystemHealth fetch error → retry button
- Frontend: React render crash → ErrorBoundary fallback UI

### 20. Cache with TTL / Guard Mutex
**Files:** `recorder.py:36`, `telegram_bot.py:23-41`, `routes_system.py:43-44`, `cloud_sync.py:40-58`, `notificationSounds.js:9-16`, `cloud_sync.py:61`, `routes_system.py:41-42`, `database.py:131`

Cached values with different TTL strategies:

| What | TTL | Location |
|------|-----|----------|
| HW encoder detection | Permanent | `recorder.py:36` |
| Bot token | 5 minutes | `telegram_bot.py:25` |
| GitHub update check | 1 hour | `routes_system.py:44` |
| Google Drive creds | Until file modified (mtime) | `cloud_sync.py:40-58` |
| Notification sounds | 600ms cooldown | `notificationSounds.js:9-16` |

Guard mutexes prevent concurrent execution: `_sync_lock` (cloud sync), `_update_lock` + `_is_updating` (system update), `_init_lock` (DB initialization).

---

## Frontend Architecture (11 patterns)

### 21. Container / Presentational Component
**File:** `App.jsx` (container) vs children (presentational)

App.jsx holds ALL application state (~60 `useState` hooks). Children receive data and callbacks via props. Pure presentational components: `AdminDashboard`, `MtxFallback`. Semi-container: `Dashboard`, `SystemHealth` (fetch own chart/health data).

### 22. Ref Synchronization (Stale Closure Prevention)
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

### 23. Role-Based Access Control (RBAC)
**File:** `App.jsx` (23+ guard locations), `Dashboard.jsx`, `SystemHealth.jsx`

- `requestAdminAccess()` gateway with password re-confirmation
- Conditional rendering: admin sees grid view, tab navigation, all stations, delete records, settings
- Operator sees: assigned station only, barcode simulator, limited controls
- `viewMode` auto-set to `'grid'` for admin on login

### 24. State Machine (Recording Flow)
**File:** `App.jsx`

```
idle → packing  (scan START response / SSE RECORDING event)
packing → idle  (SSE PROCESSING/READY/FAILED/DELETED)
packing → idle  (scan error response)
```

Ref-based guard: `packingStatusRef.current` checked in barcode handler to prevent double-scan.

### 25. AbortController Pattern (Cancellable Fetches)
**File:** `App.jsx:279, 667-684`

Cancel previous fetch when filter changes:

```javascript
if (abortControllerRef.current) abortControllerRef.current.abort();
abortControllerRef.current = new AbortController();
// ... fetch with signal, detect axios.isCancel in catch
```

### 26. Error Boundary
**File:** `App.jsx:179-202`

Class component wraps entire App. Catches React render errors, shows fallback UI.

### 27. Guard / Protected Route Pattern
**File:** `App.jsx:1015-1112`

Three sequential gates as early returns:
1. Auth loading spinner (token restore in progress)
2. Login form (no currentUser)
3. Station selection (OPERATOR without station)

Plus: must-change-password enforcement, 401 interceptor auto-logout.

### 28. Tab / Strategy UI
**Files:** `App.jsx:227`, `Dashboard.jsx:94`, `UserManagementModal.jsx:55`

State-driven tab switching changes rendered content strategy:

| Component | State | Tabs |
|-----------|-------|------|
| App.jsx | `adminTab` | Vận hành / Tổng quan |
| Dashboard | `dashTab` | Analytics / Health |
| UserManagementModal | `activeTab` | Users / Sessions / Logs |

Combined with `viewMode` (single/grid) × `role` (ADMIN/OPERATOR) × `cameraMode` (single/dual/pip) for a multi-axis rendering matrix.

### 29. Form Validation (Touched-State Pattern)
**File:** `SetupModal.jsx:125-206`

- `touched` state tracks which fields user interacted with
- `validate()` returns array of error codes
- `fieldBorder()` renders color based on touched + error state
- Server-side conflict check with debounce (300ms)
- IP/MAC validators: `isValidIPv4`, `isValidIPv6`, `isValidMAC`

---

## Testing & CI/CD (7 patterns)

### 30. Shared Fixtures (conftest.py)
**File:** `tests/conftest.py`

Layered fixture chain:

```
isolate_db → admin_user_id → admin_token → admin_headers
isolate_db → operator_user_id → operator_token → operator_headers
isolate_db + client (monkeypatches api shared state + patches CameraStreamManager)
```

### 31. Test Isolation (tmp_path + Fresh DB Per Test)
**File:** `tests/conftest.py:28-34`

`isolate_db` fixture redirects `database.DB_FILE` to `tmp_path/test.db`, resets ALL shared mutable state to empty dicts. `database.py:131-133` ensures re-init when DB path changes.

### 32. Mock / Stub Pattern
**Files:** `test_recorder.py`, `test_video_worker.py`, `test_auto_stop_timer.py`, `test_cloud_sync.py`, `test_telegram.py`

- `subprocess.Popen` / `subprocess.run` for FFmpeg mocking
- `sys.modules.setdefault(_mod, MagicMock())` for heavy deps (telebot, psutil)
- `patch.object(api, "notify_sse")` captures SSE events for assertion
- `patch("requests.post")` for Telegram API

### 33. CI Pipeline with Gates
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

### 34. Path-Based CI Skip + Caching
**File:** `.github/workflows/ci.yml:21-37, 92-97, 119-121`

`dorny/paths-filter` detects python/frontend/docs-only groups. Docs-only changes skip all gates. Pip cache keyed by `hashFiles('requirements*.txt')`. npm cache via `package-lock.json`.

### 35. Pre-commit Hook Chain
**File:** `.pre-commit-config.yaml`

5 stages: Ruff lint+format → detect-secrets → ai-sync enforcement → branch protection → pytest+eslint+prettier. Plus git-hooks `check-protected-branch.py` blocks pushes to master/dev.

### 36. Version Consistency CI
**Files:** `scripts/check_version_consistency.py`, `scripts/bump_version.py`

Cross-checks VERSION vs api.py header vs package.json vs README.md. Fails CI on mismatch. `bump_version.py` updates all locations atomically.

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
