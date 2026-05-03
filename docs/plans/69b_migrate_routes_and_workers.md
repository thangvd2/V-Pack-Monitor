# Plan 69B: Migrate Route Modules + video_worker to `state.X`

> **Status:** READY
> **Priority:** HIGH — Step 2B of restructuring
> **Scope:** 5 file updates (mechanical import changes)
> **Estimated Effort:** 20 min

---

## Prerequisites

- Plan 69A (state.py + backward compat) MUST be done
- All tests pass with backward-compat re-exports

---

## Goal

Change all 5 production consumers from `api.X` → `state.X`. Remove `import api` where it was only used for shared state.

---

## Step 1: Update `routes_auth.py`

**Current** (2 references):
```python
import api
# ... uses: api._login_attempts_lock
```

**After**:
```python
from vpack import state
# ... uses: state._login_attempts_lock
```

**NOTE**: `_login_attempts` itself is local to `routes_auth.py` — no change needed for it.

---

## Step 2: Update `routes_records.py` (heaviest — ~30 references)

**Current**:
```python
import api
# ... uses ~30 api.X references
```

**After**:
```python
from vpack import state
# ... change ALL api.X to state.X
```

Complete list of `api.X` references to change:
- `api._cancel_recording_timer` → `state._cancel_recording_timer`
- `api._recording_timers_lock` → `state._recording_timers_lock`
- `api._recording_start_times` → `state._recording_start_times`
- `api._processing_lock` → `state._processing_lock`
- `api._processing_count` → `state._processing_count`
- `api.notify_sse` → `state.notify_sse`
- `api._recorders_lock` → `state._recorders_lock`
- `api.active_recorders` → `state.active_recorders`
- `api.active_waybills` → `state.active_waybills`
- `api.active_record_ids` → `state.active_record_ids`
- `api._preflight_checks` → `state._preflight_checks`
- `api._streams_lock` → `state._streams_lock`
- `api.stream_managers` → `state.stream_managers`
- `api.get_rtsp_url` → `state.get_rtsp_url`
- `api.get_rtsp_sub_url` → `state.get_rtsp_sub_url`
- `api._station_locks_lock` → `state._station_locks_lock`
- `api._station_locks` → `state._station_locks`
- `api._RECORDING_WARNING_SECONDS` → `state._RECORDING_WARNING_SECONDS`
- `api._emit_recording_warning` → `state._emit_recording_warning`
- `api._recording_warning_timers` → `state._recording_warning_timers`
- `api._MAX_RECORDING_SECONDS` → `state._MAX_RECORDING_SECONDS`
- `api._auto_stop_recording` → `state._auto_stop_recording`
- `api._recording_timers` → `state._recording_timers`
- `api.MTX_API` → `state.MTX_API`
- `api._sse_lock` → `state._sse_lock`
- `api._sse_clients` → `state._sse_clients`
- `api.MAX_SSE_CLIENTS` → `state.MAX_SSE_CLIENTS`

**USE FIND-AND-REPLACE**: `api.` → `state.` (only for lines that import api for state). Double-check each replacement — some lines may use `api` for other purposes (there are none in this file, but verify).

---

## Step 3: Update `routes_stations.py` (~25 references)

**Current**:
```python
import api
# ... uses ~25 api.X references
```

**After**:
```python
from vpack import state
# ... change ALL api.X to state.X
```

Complete list:
- `api._processing_lock` → `state._processing_lock`
- `api._processing_count` → `state._processing_count`
- `api._camera_health_lock` → `state._camera_health_lock`
- `api._camera_health` → `state._camera_health`
- `api.get_rtsp_url` → `state.get_rtsp_url`
- `api.get_rtsp_sub_url` → `state.get_rtsp_sub_url`
- `api.CameraStreamManager` → `state.CameraStreamManager`
- `api._streams_lock` → `state._streams_lock`
- `api.stream_managers` → `state.stream_managers`
- `api._mtx_remove_path` → `state._mtx_remove_path`
- `api._recorders_lock` → `state._recorders_lock`
- `api.active_recorders` → `state.active_recorders`
- `api.active_waybills` → `state.active_waybills`
- `api.active_record_ids` → `state.active_record_ids`
- `api.reconnect_status` → `state.reconnect_status`
- `api._station_locks_lock` → `state._station_locks_lock`
- `api._station_locks` → `state._station_locks`

---

## Step 4: Update `routes_system.py` (~15 references)

**Current**:
```python
import api
# ... uses ~15 api.X references
```

**After**:
```python
from vpack import state
# ... change ALL api.X to state.X
```

Complete list:
- `api.notify_sse` → `state.notify_sse`
- `api._recorders_lock` → `state._recorders_lock`
- `api.active_recorders` → `state.active_recorders`
- `api._streams_lock` → `state._streams_lock`
- `api.stream_managers` → `state.stream_managers`
- `api.get_rtsp_url` → `state.get_rtsp_url`
- `api.get_rtsp_sub_url` → `state.get_rtsp_sub_url`
- `api.MAX_UPLOAD_SIZE` → `state.MAX_UPLOAD_SIZE`
- `api._SERVER_START_TIME` → `state._SERVER_START_TIME`
- `api._cache_lock` → `state._cache_lock`
- `api._read_version` → `state._read_version`
- `api._parse_semver` → `state._parse_semver`

---

## Step 5: Update `video_worker.py` (lazy imports, 3 references)

**Current** (lines 58, 72 — lazy imports inside functions):
```python
def _decrement_processing(...):
    import api
    with api._processing_lock:
        api._processing_count[...] ...

def _notify_sse_safe(...):
    import api
    api.notify_sse(...)
```

**After**:
```python
def _decrement_processing(...):
    from vpack import state
    with state._processing_lock:
        state._processing_count[...] ...

def _notify_sse_safe(...):
    from vpack import state
    state.notify_sse(...)
```

Keep the lazy import pattern (import inside function) — don't move to top-level.

---

## Verification

1. `pytest tests/ -v` — ALL tests pass (backward-compat in api.py still covers test files)
2. `ruff check routes_auth.py routes_records.py routes_stations.py routes_system.py video_worker.py` — no errors
3. `grep -n "import api" routes_auth.py routes_records.py routes_stations.py routes_system.py` — returns 0 results
4. `grep -n "import api" video_worker.py` — returns 0 results (or only imports for non-state purposes)
5. `grep -n "api\." routes_auth.py routes_records.py routes_stations.py routes_system.py video_worker.py` — returns 0 results

## After This Plan

All 5 production consumers use `state.X`. Backward-compat re-exports in `api.py` still exist for test files. Tests still pass via backward compat.
