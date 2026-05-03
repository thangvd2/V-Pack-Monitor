# Plan 69A: Create `vpack/state.py` + Backward-Compat Re-exports

> **Status:** READY
> **Priority:** HIGH — Step 2A of restructuring
> **Scope:** 1 new file + 1 file update
> **Estimated Effort:** 20 min

---

## Prerequisites

- Plan 68 (skeleton) MUST be done

---

## Goal

Extract all shared state from `api.py` into `vpack/state.py`. Add backward-compat re-exports in `api.py` so all existing `api.X` references still work. **No consumer files change yet.**

---

## Step 1: Create `vpack/state.py`

Create new file. Move ALL of the following from `api.py`:

### State Variables

```python
# Dicts / collections
active_recorders = {}        # used by routes_stations, routes_records, routes_system
active_waybills = {}         # used by routes_stations, routes_records
active_record_ids = {}       # used by routes_stations, routes_records
_processing_count = {}       # NOTE: dict, not int!
reconnect_status = {}        # used by routes_stations
_camera_health = {}          # used by routes_stations
_sse_clients = []            # NOTE: list, not set! Uses .append(), .remove(), .pop()

# Timers
_recording_timers = {}
_recording_start_times = {}
_recording_warning_timers = {}

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
_RECORDING_WARNING_SECONDS = 540          # 9 minutes

# Logger
_logger = logging.getLogger("vpack")
```

### Helper Functions

```python
get_rtsp_url(stream_key, ...)
get_rtsp_sub_url(stream_key, ...)
notify_sse(event_type, data)
_read_version()
_parse_semver(version_str)
_cancel_recording_timer(station_id)
_preflight_checks(station_id)
_auto_stop_recording(station_id)
_emit_recording_warning(station_id)
_mtx_remove_path(stream_key)
_mtx_add_path(stream_key, cam_index)    # Coupled with CameraStreamManager
```

### Class

```python
CameraStreamManager    # Coupled with _mtx_add_path
```

Add necessary imports at top of `state.py`: `threading`, `time`, `os`, `logging`, plus any other imports these functions/class need (check their implementations in `api.py`).

### Functions That STAY in `api.py` (do NOT extract)

- `_mtx_cleanup_orphaned_paths()` — only called by lifespan
- `_recover_pending_records()` — only called by lifespan (patched in tests as `api._recover_pending_records`)
- `_get_video_info_external()` — only called by `_recover_pending_records` (patched in tests)
- `_get_cors_origins()` — only called internally
- `lifespan()` — FastAPI context manager

---

## Step 2: Update `api.py`

1. **Remove** all extracted code (variables, functions, class)
2. **Add** backward-compat re-exports at module level:

```python
from vpack import state

# Backward-compat re-exports — allows existing `api.X` to keep working
# until all consumers are migrated to `state.X` in Plans 69B/69C.
_active_recorders = state.active_recorders
active_waybills = state.active_waybills
# ... (re-export ALL extracted names)
```

**IMPORTANT**: The re-export pattern must cover every name that other modules access via `api.X`. The complete list (from audit):

```
active_recorders, active_waybills, active_record_ids, _processing_count,
reconnect_status, _camera_health, _sse_clients,
_recording_timers, _recording_start_times, _recording_warning_timers,
_streams_lock, _recorders_lock, _processing_lock, _station_locks_lock,
_recording_timers_lock, _login_attempts_lock, _camera_health_lock,
_sse_lock, _cache_lock, _station_locks,
MTX_API, MAX_UPLOAD_SIZE, MAX_SSE_CLIENTS, _SERVER_START_TIME,
_MAX_RECORDING_SECONDS, _RECORDING_WARNING_SECONDS,
get_rtsp_url, get_rtsp_sub_url, notify_sse,
_read_version, _parse_semver, _cancel_recording_timer,
_preflight_checks, _auto_stop_recording, _emit_recording_warning,
_mtx_remove_path, CameraStreamManager
```

3. In `api.py`'s `lifespan()` and remaining functions, change direct references to `state.X`:

```python
# BEFORE (inside lifespan):
stream_managers[...] = CameraStreamManager(...)
_mtx_cleanup_orphaned_paths()

# AFTER (inside lifespan):
state.stream_managers[...] = state.CameraStreamManager(...)
state._mtx_cleanup_orphaned_paths()  # This stays in api.py, no change needed
```

Wait — `_mtx_cleanup_orphaned_paths` stays in api.py, so no `state.` prefix needed for it. Only references to extracted state need `state.` prefix.

4. Keep route registration unchanged:
```python
import routes_auth
import routes_records
import routes_stations
import routes_system
# ... register_routes(app) calls unchanged
```

---

## Verification

1. `ruff check api.py vpack/state.py` — no errors
2. `python -c "from vpack import state; print(len([x for x in dir(state) if not x.startswith('__')]))"` — shows all extracted symbols
3. `pytest tests/ -v` — ALL tests still pass (backward-compat ensures nothing breaks)
4. `python -c "import api; print(api.active_recorders)"` — backward-compat works, returns `{}`
5. `python -c "import api; print(api.get_rtsp_url)"` — backward-compat works, function is callable

## After This Plan

`vpack/state.py` exists with all shared state. `api.py` re-exports everything. All existing code still uses `api.X` and works. Plans 69B/69C will migrate consumers to `state.X`.
