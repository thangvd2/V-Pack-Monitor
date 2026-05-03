# Plan 69: Extract Shared State from `api.py` → `vpack/state.py`

> **Status:** READY
> **Priority:** HIGH — Step 2 of restructuring (CRITICAL)
> **Scope:** 1 new file + 10 file updates
> **Estimated Effort:** 60 min

---

## Goal

Extract all shared state (dicts, locks, timers, constants) from `api.py` into `vpack/state.py`. Route modules and other consumers change `api.X` → `state.X`. This is the **biggest and riskiest** change in the entire restructuring.

**No files move** in this plan. Everything stays at root. Only the import source changes.

---

## What to Extract

### State Variables (from `api.py`)

```python
# Dicts / collections
active_recorders = {}        # routes_stations, routes_records, routes_system
active_waybills = {}         # routes_stations, routes_records
active_record_ids = {}       # routes_stations, routes_records
_processing_count = {}       # routes_stations, routes_records — NOTE: dict, not int!
reconnect_status = {}        # routes_stations
_camera_health = {}          # routes_stations
_sse_clients = []            # routes_records — NOTE: list, not set! Uses .append(), .remove(), .pop()

# Timers
_recording_timers = {}           # routes_records
_recording_start_times = {}      # routes_records
_recording_warning_timers = {}   # routes_records

# Locks
_streams_lock = threading.Lock()
_recorders_lock = threading.Lock()
_processing_lock = threading.Lock()
_station_locks_lock = threading.Lock()
_recording_timers_lock = threading.Lock()
_login_attempts_lock = threading.Lock()
_camera_health_lock = threading.Lock()
_sse_lock = threading.Lock()
_cache_lock = threading.Lock()

# Station locks dict
_station_locks = {}

# Config constants
MTX_API = os.environ.get("MTX_API", "http://127.0.0.1:9997")
MAX_UPLOAD_SIZE = 1 * 1024 * 1024        # 1MB
MAX_SSE_CLIENTS = 50
_SERVER_START_TIME = time.time()
_MAX_RECORDING_SECONDS = 600
_RECORDING_WARNING_SECONDS = 540          # 9 minutes (NOT 30!)

# Logger
_logger = logging.getLogger("vpack")
```

**NOTE**: `_login_attempts = {}` is defined in `routes_auth.py` (line 26), NOT in `api.py`. Only `_login_attempts_lock` is in `api.py`. Do NOT extract `_login_attempts` — it stays in `routes_auth.py`.

### Helper Functions (from `api.py`)

```python
get_rtsp_url(stream_key, ...)           # routes_stations, routes_records, routes_system
get_rtsp_sub_url(stream_key, ...)       # routes_stations, routes_records, routes_system
notify_sse(event_type, data)            # routes_records, routes_system, video_worker
_read_version()                         # routes_system
_parse_semver(version_str)              # routes_system
_cancel_recording_timer(station_id)     # routes_records
_preflight_checks(station_id)           # routes_records
_auto_stop_recording(station_id)        # routes_records
_emit_recording_warning(station_id)     # routes_records
_mtx_remove_path(stream_key)            # routes_stations
_mtx_add_path(stream_key, cam_index)    # Only used by CameraStreamManager — extract together
_mtx_cleanup_orphaned_paths()           # Only used by lifespan — KEEP in api.py
_get_video_info_external(url)           # Only used by _recover_pending_records — extract together
_recover_pending_records()              # Called by lifespan — KEEP in api.py (but imports state)
```

**Decision**: Extract `_mtx_add_path` with `CameraStreamManager` (they're coupled). Keep `_mtx_cleanup_orphaned_paths` and `_recover_pending_records` in `api.py` — they're called by lifespan only. `_get_video_info_external` stays too (it's only used by `_recover_pending_records`). But test files patch `_get_video_info_external` via `api._get_video_info_external`, so if it stays in api.py, no test changes needed.

### Class

```python
CameraStreamManager            # routes_stations, tests/conftest
```

Extract with `_mtx_add_path` since CameraStreamManager calls it.

---

## Changes

### 1. Create `vpack/state.py`

Move all variables, functions, and class listed above from `api.py` into `vpack/state.py`. Add necessary imports at top (threading, time, os, logging, etc.).

### 2. Update `api.py`

- Remove all extracted code
- Add `from vpack import state` (or `import vpack.state as state`)
- In `api.py` lifespan and remaining helpers, change to `state.X`
- Keep route registration (`routes_*.register_routes(app)`) in `api.py`
- Keep `_mtx_cleanup_orphaned_paths`, `_recover_pending_records`, `_get_video_info_external`, `lifespan` in `api.py`

### 3. Update `routes_auth.py`

Change: `import api` + `api._login_attempts_lock`
To: `from vpack import state` + `state._login_attempts_lock`

Note: `_login_attempts` itself is already local to `routes_auth.py` — no change needed for it.

### 4. Update `routes_records.py`

Change: `import api` + all `api.X` references (~30 references)
To: `from vpack import state` + `state.X`

This file has the MOST references to shared state. Variables accessed:
- `api._cancel_recording_timer`, `api._recording_timers_lock`, `api._recording_start_times`
- `api._processing_lock`, `api._processing_count`, `api.notify_sse`
- `api._recorders_lock`, `api.active_recorders`, `api.active_waybills`, `api.active_record_ids`
- `api._preflight_checks`, `api._streams_lock`, `api.stream_managers`
- `api.get_rtsp_url`, `api.get_rtsp_sub_url`
- `api._station_locks_lock`, `api._station_locks`
- `api._RECORDING_WARNING_SECONDS`, `api._emit_recording_warning`, `api._recording_warning_timers`
- `api._MAX_RECORDING_SECONDS`, `api._auto_stop_recording`, `api._recording_timers`
- `api.MTX_API`, `api._sse_lock`, `api._sse_clients`, `api.MAX_SSE_CLIENTS`

### 5. Update `routes_stations.py`

Change: `import api` + all `api.X` references (~25 references)
To: `from vpack import state` + `state.X`

Variables accessed:
- `api._processing_lock`, `api._processing_count`, `api._camera_health_lock`, `api._camera_health`
- `api.get_rtsp_url`, `api.get_rtsp_sub_url`, `api.CameraStreamManager`
- `api._streams_lock`, `api.stream_managers`, `api._mtx_remove_path`
- `api._recorders_lock`, `api.active_recorders`, `api.active_waybills`, `api.active_record_ids`
- `api.reconnect_status`, `api._station_locks_lock`, `api._station_locks`

### 6. Update `routes_system.py`

Change: `import api` + all `api.X` references (~15 references)
To: `from vpack import state` + `state.X`

Variables accessed:
- `api.notify_sse`, `api._recorders_lock`, `api.active_recorders`
- `api._streams_lock`, `api.stream_managers`
- `api.get_rtsp_url`, `api.get_rtsp_sub_url`, `api.MAX_UPLOAD_SIZE`
- `api._SERVER_START_TIME`, `api._cache_lock`
- `api._read_version`, `api._parse_semver`

### 7. Update `video_worker.py` (**MISSED IN ORIGINAL PLAN**)

This file has **lazy imports** of `api` inside functions (lines 58, 72):
- `api._processing_lock`, `api._processing_count` (inside `_decrement_processing()`)
- `api.notify_sse` (inside `_notify_sse_safe()`)

Change: `import api` (lazy) → `from vpack import state` (lazy or top-level)
Change: `api._processing_lock` → `state._processing_lock`, etc.

### 8. Update `tests/conftest.py` (**MISSED IN ORIGINAL PLAN**)

This file imports `api` and monkeypatches **10+** `api.X` attributes:
- `api.stream_managers`, `api.active_recorders`, `api.active_waybills`
- `api.active_record_ids`, `api._processing_count`, `api._station_locks`
- `api.reconnect_status`, `api._recording_timers`, `api._recording_start_times`
- `api._recording_warning_timers`, `api.CameraStreamManager`, `api.app`

Change all `api.X` monkeypatches to `state.X` where X is extracted state.
Keep `api.app` reference (the FastAPI app stays in api.py).

### 9. Update `tests/test_api_helpers.py` (**MISSED IN ORIGINAL PLAN**)

```python
# BEFORE:
from api import get_rtsp_sub_url, get_rtsp_url

# AFTER:
from vpack.state import get_rtsp_sub_url, get_rtsp_url
```

### 10. Update `tests/test_auto_stop_timer.py` (**MISSED IN ORIGINAL PLAN**)

This file has **30+** `api.X` references:
- `api.active_record_ids`, `api._recording_timers`, `api._recording_warning_timers`
- `api._recording_start_times`, `api.active_recorders`, `api.active_waybills`
- `api._processing_count`, `api._auto_stop_recording`, `api._emit_recording_warning`
- `api._cancel_recording_timer`, `api._recording_timers_lock`

Change all to `state.X` references.

### 11. Update `tests/test_video_worker.py` (**MISSED IN ORIGINAL PLAN**)

Patches `"api._get_video_info_external"` and calls `api._recover_pending_records()`.

Since `_get_video_info_external` and `_recover_pending_records` STAY in `api.py` (not extracted), these references remain `api.X`. No change needed in this file — but MUST verify this is correct.

---

## IMPORTANT: Route Registration Pattern

Route modules receive `app` from `api.py` — they do NOT import `api` for the app object. They imported `api` only for shared state. After this plan, they import `state` instead:

```python
def register_routes(app):
    @app.get("/api/...")
    def handler(...):
        ...
```

---

## Functions That STAY in `api.py`

These functions are only called by `lifespan()` or internally — they are NOT accessed by other modules via `api.X`:

- `_mtx_cleanup_orphaned_paths()` — only called by lifespan
- `_recover_pending_records()` — only called by lifespan (but patched in tests as `api._recover_pending_records`)
- `_get_video_info_external()` — only called by `_recover_pending_records` (but patched in tests as `api._get_video_info_external`)
- `_get_cors_origins()` — only called internally
- `lifespan()` — FastAPI app context manager

**Note**: `_recover_pending_records` and `_get_video_info_external` are patched in `tests/test_video_worker.py` via `api._recover_pending_records` and `"api._get_video_info_external"`. Since they stay in `api.py`, these test patches remain unchanged.

---

## Verification

1. `pytest tests/ -v` — ALL tests pass (this is critical)
2. `ruff check .` — no errors
3. `python -c "from vpack import state; print(dir(state))"` — shows all extracted symbols
4. Manual: start server, test recording, test ping, test station CRUD
5. No `api.X` attribute access remains in any `routes_*.py` file (except `api.app` if needed)
6. No `api.X` attribute access remains in `video_worker.py` for state variables

## After This Plan

`api.py` is significantly slimmer. Route modules and `video_worker.py` import from `vpack.state` instead of `api`. All files still at root.
