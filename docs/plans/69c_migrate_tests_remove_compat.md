# Plan 69C: Migrate Test Files + Remove Backward-Compat Re-exports

> **Status:** READY
> **Priority:** HIGH — Step 2C of restructuring
> **Scope:** 5 file updates + 1 cleanup
> **Estimated Effort:** 20 min

---

## Prerequisites

- Plan 69A (state.py + backward compat) MUST be done
- Plan 69B (route modules migrated) MUST be done
- All tests still pass via backward-compat

---

## Goal

Migrate 4 test files from `api.X` → `state.X`. Then remove backward-compat re-exports from `api.py`.

---

## Step 1: Update `tests/conftest.py`

**Current**: `import api` + monkeypatches 10+ `api.X` attributes:
- `api.stream_managers`, `api.active_recorders`, `api.active_waybills`
- `api.active_record_ids`, `api._processing_count`, `api._station_locks`
- `api.reconnect_status`, `api._recording_timers`, `api._recording_start_times`
- `api._recording_warning_timers`, `api.CameraStreamManager`

**After**:
```python
from vpack import state
# ... change monkeypatch targets from api.X to state.X
# e.g., monkeypatch.setattr(api, "stream_managers", {}) → monkeypatch.setattr(state, "stream_managers", {})
```

**KEEP** `import api` or `from api import app` — the FastAPI `app` object stays in `api.py`. Only state references change.

---

## Step 2: Update `tests/test_api_helpers.py`

**Current**:
```python
from api import get_rtsp_sub_url, get_rtsp_url
```

**After**:
```python
from vpack.state import get_rtsp_sub_url, get_rtsp_url
```

---

## Step 3: Update `tests/test_auto_stop_timer.py` (heaviest — ~30 references)

**Current**: `import api` + 30+ `api.X` references:
- `api.active_record_ids`, `api._recording_timers`, `api._recording_warning_timers`
- `api._recording_start_times`, `api.active_recorders`, `api.active_waybills`
- `api._processing_count`, `api._auto_stop_recording`, `api._emit_recording_warning`
- `api._cancel_recording_timer`, `api._recording_timers_lock`

**After**:
```python
from vpack import state
# ... change ALL api.X → state.X for state variables
# KEEP any references to api.app or api database if present
```

---

## Step 4: Verify `tests/test_video_worker.py` (may need NO changes)

This file patches `"api._get_video_info_external"` and calls `api._recover_pending_records()`.

Since `_get_video_info_external` and `_recover_pending_records` **STAY in api.py** (not extracted to state), these references should remain `api.X`. Verify this is correct — no changes needed.

---

## Step 5: Remove backward-compat re-exports from `api.py`

After all consumers are migrated, remove the re-export block added in Plan 69A:

```python
# DELETE THIS ENTIRE BLOCK:
from vpack import state
active_recorders = state.active_recorders
active_waybills = state.active_waybills
# ... (all re-exports)
```

Replace with a clean import:
```python
from vpack import state as _state  # Only if api.py still needs to reference state internally
```

Or just direct imports where api.py's own code needs them:
```python
from vpack.state import _logger, _SERVER_START_TIME  # etc. only what api.py itself uses
```

---

## Verification

1. `pytest tests/ -v` — ALL tests pass
2. `ruff check .` — no errors
3. `grep -rn "api\." tests/conftest.py tests/test_api_helpers.py tests/test_auto_stop_timer.py` — 0 state-related references (only `api.app` or `api._recover_pending_records` if applicable)
4. `grep -n "active_recorders = state" api.py` — backward-compat re-exports are GONE
5. `python -c "from vpack import state; print(state.active_recorders)"` — state.py works independently

## After This Plan

State extraction complete. All consumers use `vpack.state`. No backward-compat re-exports remain. `api.py` is significantly slimmer. All files still at root.
