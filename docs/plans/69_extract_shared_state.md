# Plan 69: Extract Shared State from `api.py` → `vpack/state.py`

> **Status:** READY
> **Priority:** HIGH — Step 2 of restructuring (CRITICAL)
> **Scope:** 1 new file + 5 file updates
> **Estimated Effort:** 45 min

---

## Goal

Extract all shared state (dicts, locks, timers, constants) from `api.py` into `vpack/state.py`. Route modules change `api.X` → `state.X`. This is the **biggest and riskiest** change in the entire restructuring.

**No files move** in this plan. Everything stays at root. Only the import source changes.

---

## What to Extract

### State Variables (from `api.py`)

```python
# Dicts / collections
stream_managers = {}        # routes_stations, routes_records, routes_system
active_recorders = {}       # routes_stations, routes_records, routes_system
active_waybills = {}        # routes_stations, routes_records
active_record_ids = {}      # routes_stations, routes_records
reconnect_status = {}       # routes_stations
_processing_count = 0       # routes_stations, routes_records
_camera_health = {}         # routes_stations
_sse_clients = set()        # routes_records
_login_attempts = {}        # routes_auth

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
_station_locks = {}

# Station locks dict
_station_locks = {}

# Config constants
MTX_API = "..."
MAX_UPLOAD_SIZE = 100 * 1024 * 1024
MAX_SSE_CLIENTS = 50
_SERVER_START_TIME = time.time()
_MAX_RECORDING_SECONDS = 600
_RECORDING_WARNING_SECONDS = 30
```

### Helper Functions (from `api.py`)

```python
get_rtsp_url(stream_key, ...)       # routes_stations, routes_records, routes_system
get_rtsp_sub_url(stream_key, ...)   # routes_stations, routes_records, routes_system
notify_sse(event_type, data)        # routes_records, routes_system
_read_version()                     # routes_system
_parse_semver(version_str)          # routes_system
_cancel_recording_timer(station_id) # routes_records
_preflight_checks(station_id)       # routes_records
_auto_stop_recording(station_id)    # routes_records
_emit_recording_warning(station_id) # routes_records
_mtx_remove_path(stream_key)        # routes_stations
```

### Class

```python
CameraStreamManager            # routes_stations
```

---

## Changes

### 1. Create `vpack/state.py`

Move all variables, functions, and class listed above from `api.py` into `vpack/state.py`. Add necessary imports at top (threading, time, os, etc.).

### 2. Update `api.py`

- Remove all extracted code
- Add `from vpack import state` (or `import vpack.state as state`)
- In `api.py` lifespan and helpers that use these variables, change to `state.X`
- Keep route registration (`routes_*.register_routes(app)`) in `api.py`

### 3. Update `routes_auth.py`

Change: `import api` + `api._login_attempts`, `api._login_attempts_lock`
To: `from vpack import state` + `state._login_attempts`, `state._login_attempts_lock`

### 4. Update `routes_records.py`

Change: `import api` + all `api.X` references (~20 references)
To: `from vpack import state` + `state.X`

This file has the MOST references to shared state.

### 5. Update `routes_stations.py`

Change: `import api` + all `api.X` references (~15 references)
To: `from vpack import state` + `state.X`

### 6. Update `routes_system.py`

Change: `import api` + all `api.X` references (~10 references)
To: `from vpack import state` + `state.X`

---

## IMPORTANT: Keep `import api` for route registration

Route modules still need to register routes. The pattern is:
```python
def register_routes(app):
    @app.get("/api/...")
    def handler(...):
        ...
```

They receive `app` from `api.py` — they do NOT import `api` for the app object. They imported `api` only for shared state. After this plan, they import `state` instead.

---

## Verification

1. `pytest tests/ -v` — ALL tests pass (this is critical)
2. `ruff check .` — no errors
3. `python -c "from vpack import state; print(dir(state))"` — shows all extracted symbols
4. Manual: start server, test recording, test ping, test station CRUD
5. No `api.X` attribute access remains in any `routes_*.py` file

## After This Plan

`api.py` is significantly slimmer. Route modules import from `vpack.state` instead of `api`. All files still at root.
