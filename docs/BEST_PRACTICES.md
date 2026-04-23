# Best Practices — V-Pack Monitor v3.4.0

> Coding conventions, standard techniques, and tooling choices applied throughout the codebase.
> Related: [DESIGN_PATTERNS.md](./DESIGN_PATTERNS.md) for architectural design patterns.

---

## Classification Summary

| Category | Count | Description |
|----------|-------|-------------|
| Security | 4 | Input validation, encryption, access tokens, timer safety |
| Frontend Conventions | 10 | State management, debouncing, polling, cleanup, React hooks |
| Standard Techniques | 6 | Middleware, modals, CRUD, memoization, composition |
| Testing | 2 | Test parameterization and organization |
| Infrastructure | 4 | Docker, packaging, monorepo, feature flags |
| Concurrency | 2 | Backoff, parallel execution |

---

## Security (4 items)

### Path Traversal Defense
**Files:** `routes_records.py:272-275`, `recorder.py:173-178`, `routes_system.py:270-276`, `database.py:869-870`

- Waybill code sanitization (strip special chars)
- Download path validation (prevent `../` traversal)
- Zip Slip prevention (validate extracted paths stay within target dir)
- SQL column whitelist

### JWT + Token Revocation
**File:** `auth.py`

Access tokens (15min) + Refresh tokens (7days). Revocation list stored in DB. `get_current_user()` checks revocation on every request.

### Secret Management (Encryption at Rest)
**File:** `database.py:27-56`

Fernet encryption for sensitive settings (bot token, cloud credentials). Key derived from JWT secret. `_SENSITIVE_KEYS` whitelist determines which settings to encrypt.

### Auto-stop Timer Safety
**File:** `api.py:78-81, 334-409`

Warning timer (540s) → SSE `recording_warning` event. Stop timer (600s) → auto-stop recording. Critical safety check at L353: `if current_record_id == record_id` prevents stopping wrong recording.

---

## Frontend Conventions (10 items)

### Lift State Up
**File:** `App.jsx` (55+ useState)

ALL significant state lives in App.jsx. No child manages shared state. Everything flows via props. Note: this creates a 2200+ line container — extraction candidates include `useSSE()`, `useAuth()`, `useToast()`, `useDebouncedFetch()`.

### Debouncing / Throttling
**Files:** `App.jsx`, `SetupModal.jsx`, `VideoPlayerModal.jsx`

| What | Delay | Location |
|------|-------|----------|
| Search input | 300ms | `App.jsx:49, 675` |
| Barcode buffer | 100ms | `App.jsx:46, 954` |
| Conflict check | 300ms | `SetupModal.jsx:157` |
| Video controls auto-hide | 3000ms | `VideoPlayerModal.jsx:59` |

### Polling
**Files:** `App.jsx`, `SystemHealth.jsx`, `UserManagementModal.jsx`

| What | Interval | Location |
|------|----------|----------|
| Station status | 10s | `App.jsx:63` |
| Session heartbeat | 30s | `App.jsx:353` |
| Reconnect status | 10s | `App.jsx:609` |
| System health | 5s | `SystemHealth.jsx:72` |
| Sessions/logs auto-refresh | 30s | `UserManagementModal.jsx:132` |

### Axios Interceptor (401 Auto-Logout)
**File:** `App.jsx:364-377`

Response interceptor catches 401 → auto-logout. Global timeout + Authorization header set on login.

### Confirmation Dialog
**Files:** `App.jsx:296-298, 2204-2228`, `SetupModal.jsx:867-891`

Reusable confirm dialog with `showConfirmDialog(message, onConfirm)` callback. Used for delete records, delete station, unsaved changes, conflict warnings.

### Content-Disposition Parsing
**File:** `VideoPlayerModal.jsx:288-293`

Regex extraction of filename from download headers. Handles both `filename=` and `filename*=UTF-8''` formats. Falls back to `{waybillCode}.mp4`.

### Race Guard (active flag)
**File:** `App.jsx:337, 585`

`let active = true` pattern prevents state updates after component unmount. Checked before `setState` calls. Alternative: `useRef` for mounted tracking.

### Named Constants
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

### useEffect Cleanup
**Files:** 13 useEffect cleanups across all components

Every useEffect with side effects has a cleanup function: SSE close, clearInterval, clearTimeout, removeEventListener, abort(), interceptor eject.

### Memoization (useMemo / useCallback)
**Files:** 15+ locations across all components

- `stationsIdStr` memoized from stations array (`App.jsx:379`)
- `activeStation` memoized lookup (`App.jsx:972`)
- `showToast`, `showConfirmDialog`, `doChangePassword` in useCallback
- `fetchHourly`, `fetchTrend`, `fetchStationsComparison` in Dashboard
- `fetchData` in SystemHealth

---

## Standard Techniques (6 items)

### Middleware (CORS + Exception Handler)
**File:** `api.py:542-553, 658-664`

CORS middleware with restricted methods. Custom async exception handler suppresses connection reset errors in SSE streams.

### Modal Pattern
**Files:** `VideoPlayerModal.jsx`, `SetupModal.jsx`, `UserManagementModal.jsx`

Shared structure: `if (!isOpen) return null` → backdrop click = close → `stopPropagation` on inner content. Parent controls open/close via state.

### CRUD Pattern
**File:** `UserManagementModal.jsx`

Full CRUD for users: Create (with validation) → Read (fetch on mount) → Update (inline editing) → Delete (with self-delete guard) → Toggle active → Reset password.

### Promise.allSettled for Parallel Fetches
**File:** `SystemHealth.jsx:54-58`

Fetches health + processes + network in parallel. Each result checked independently (`status === 'fulfilled'`).

### Component Composition
**File:** `Dashboard.jsx:50-84`

`StatCard` and `ChartCard` sub-components. Dashboard conditionally embeds `SystemHealth`. AdminDashboard composes `MtxFallback`.

---

## Testing (2 items)

### Parameterized by Enumeration
**File:** `test_api_helpers.py`

22 test methods covering all camera brands × channels × edge cases. Loop-based parameterization in `test_database_edge_cases.py:182-193` for SQL injection / unicode / spaces. Opportunity: migrate to `@pytest.mark.parametrize`.

### Test Organization by Concern
**Files:** 14 test files

| File | Concern |
|------|---------|
| `test_database.py` | DB layer (encryption, settings, records, stations, users) |
| `test_database_edge_cases.py` | Boundary / security |
| `test_auth.py` | JWT, token revocation, RBAC |
| `test_api_routes.py` | API integration |
| `test_api_hardening.py` | Input validation |
| `test_security_regression.py` | 18 security regression tests |
| `test_video_worker.py` | Worker lifecycle, crash recovery |
| `test_recorder.py` | FFmpeg recording modes |
| `test_video_search.py` | FTS5, pagination, filters |
| `test_auto_stop_timer.py` | Timer lifecycle |
| `test_network.py` | Network utilities |
| `test_cloud_sync.py` | Cloud backup |
| `test_telegram.py` | Telegram API |
| `test_api_helpers.py` | RTSP URL builder |

---

## Concurrency (2 items)

### Exponential Backoff
**File:** `telegram_bot.py:96-105`

Telegram bot polling retries with exponential backoff (3s → 6s → 12s → 24s → 48s → 60s cap). Resets to 3s on success.

### Parallel Execution (ThreadPoolExecutor)
**File:** `network.py:157-163`

LAN ping sweep uses `ThreadPoolExecutor(max_workers=50)` to ping all 254 hosts in a /24 subnet in parallel with `as_completed(futures, timeout=17)`.

---

## Infrastructure & Tooling (4 items)

### Docker Multi-Arch
**File:** `Dockerfile`

Runtime arch detection for MediaMTX download. Dual-process CMD: `mediamtx & python -m uvicorn api:app`. Named volumes for persistent data.

### PyInstaller Packaging
**Files:** `build.py`, `V-Pack-Monitor.spec`

3-step build: `npm run build` → install PyInstaller → bundle backend + frontend dist into single executable. Runtime detection via `getattr(sys, 'frozen', False)`.

### Monorepo Organization
**Project root**

Backend (Python/FastAPI) + frontend (React/Vite) + Docker + CI + scripts in one repo. Build script orchestrates both.

### Feature Flags / Configuration-Driven Behavior
**Files:** `database.py`, `api.py`, `routes_system.py`

- `_VALID_RECORD_STATUSES` whitelist (`database.py:476`)
- `_VALID_ROLES` whitelist (`database.py:993`)
- `LIVE_VIEW_STREAM` setting: main vs sub stream (`api.py:559`)
- `RECORD_KEEP_DAYS` validated enum: 0/3/7/15/30/60/90/150/365 (`routes_system.py:414`)
- `_MAX_RECORDING_SECONDS = 600` hard cap (`api.py:42`)
