# Plan: Auto-detect and remove broken cam2 MediaMTX paths

**Ngày**: 2026-04-22
**Mức độ**: Medium — Prevent log spam and UI confusion from broken cam2 paths
**Loại**: Reliability improvement (backend)

---

## Problem

When a station uses PIP/DUAL_FILE mode with a dual-lens camera but channel=2 is not available (firewall block, camera doesn't support channel=2, wrong brand detection), MediaMTX logs EOF errors every 5 seconds:

```
2026/04/22 00:18:29 ERR [path station_1_cam2] [RTSP source] EOF
2026/04/22 00:18:34 ERR [path station_1_cam2] [RTSP source] EOF
```

The monitor loop (`_monitor_loop`) detects the missing path and **re-registers it**, causing an infinite retry cycle. The cam2 path never works but never gets cleaned up.

---

## Solution: MediaMTX health check in monitor loop

The monitor loop already calls `GET /v3/paths/list` every 15 seconds. MediaMTX returns health information per path. Use this to detect broken cam2 paths and auto-remove them.

### MediaMTX API response (per path item)

```json
{
  "name": "station_1_cam2",
  "ready": false,           // true = stream is active
  "available": false,
  "online": false,
  "source": null,            // null = no source connected
  "tracks": [],              // empty = no video/audio tracks
  "tracks2": [],
  "readers": [],
  "inboundBytes": 0
}
```

- **Healthy path**: `ready=true`, `tracks=["video","audio"]`, `source` is present
- **Broken path** (EOF): `ready=false`, `tracks=[]`, `source` is null

---

## Files to Change (1 file)

### `api.py` — `CameraStreamManager._monitor_loop()` (lines 233-259)

#### Change 1: Add `cam2_fail_count` instance variable

**Location**: `__init__` method (line 170-177)

**Before:**
```python
def __init__(self, url, station_id=None, cam2_url=None):
    self.url = url
    self.station_id = station_id
    self.cam2_url = cam2_url
    self.is_running = False
    self.thread = None
    self._fail_count = 0
    self._lock = threading.Lock()
```

**After:**
```python
def __init__(self, url, station_id=None, cam2_url=None):
    self.url = url
    self.station_id = station_id
    self.cam2_url = cam2_url
    self.is_running = False
    self.thread = None
    self._fail_count = 0
    self._cam2_fail_count = 0  # consecutive health-check failures for cam2
    self._lock = threading.Lock()
```

#### Change 2: Rewrite cam2 check in `_monitor_loop` (lines 252-257)

**Before:**
```python
# Also check cam2 path
if self.cam2_url:
    cam2_path_name = f"station_{self.station_id}_cam2"
    cam2_found = any(p.get("name") == cam2_path_name for p in items)
    if not cam2_found:
        _mtx_add_path(self.station_id, self.cam2_url, suffix="_cam2")
```

**After:**
```python
# Check cam2 path health
if self.cam2_url:
    cam2_path_name = f"station_{self.station_id}_cam2"
    cam2_item = next((p for p in items if p.get("name") == cam2_path_name), None)

    if cam2_item and cam2_item.get("ready") is True:
        # cam2 is healthy — reset fail counter
        self._cam2_fail_count = 0
    elif cam2_item and cam2_item.get("ready") is False:
        # cam2 path exists but stream is broken (EOF, timeout, etc.)
        self._cam2_fail_count += 1
        if self._cam2_fail_count >= 2:
            logger.warning(
                f"[MTX] station_{self.station_id}_cam2 failed health check "
                f"{self._cam2_fail_count}x — removing broken cam2 path"
            )
            _mtx_remove_path(self.station_id, suffix="_cam2")
            self.cam2_url = None
            self._cam2_fail_count = 0
    else:
        # cam2 path not found in MediaMTX — re-register (existing behavior)
        _mtx_add_path(self.station_id, self.cam2_url, suffix="_cam2")
```

**Why 2 consecutive failures?**
- First failure: MediaMTX may still be connecting (initial RTSP handshake takes a few seconds)
- Second failure (30s after creation): confirmed broken — remove path
- This gives MediaMTX enough time to complete the initial connection attempt

#### Change 3: Reset `_cam2_fail_count` in `start()` method (line 182)

**Before:**
```python
def start(self):
    if not self.is_running and self.url:
        self.is_running = True
        self._fail_count = 0
        self._mtx_register()
```

**After:**
```python
def start(self):
    if not self.is_running and self.url:
        self.is_running = True
        self._fail_count = 0
        self._cam2_fail_count = 0
        self._mtx_register()
```

#### Change 4: Reset `_cam2_fail_count` in `update_cam2_url()` (lines 268-276)

**Before:**
```python
def update_cam2_url(self, new_url):
    with self._lock:
        old_cam2 = self.cam2_url
        self.cam2_url = new_url
    if old_cam2 and self.station_id:
        _mtx_remove_path(self.station_id, suffix="_cam2")
    if new_url and self.station_id:
        _mtx_add_path(self.station_id, new_url, suffix="_cam2")
    self._mtx_register()
```

**After:**
```python
def update_cam2_url(self, new_url):
    with self._lock:
        old_cam2 = self.cam2_url
        self.cam2_url = new_url
    self._cam2_fail_count = 0  # reset health counter on URL change
    if old_cam2 and self.station_id:
        _mtx_remove_path(self.station_id, suffix="_cam2")
    if new_url and self.station_id:
        _mtx_add_path(self.station_id, new_url, suffix="_cam2")
    self._mtx_register()
```

---

## Files NOT Changed

| File | Reason |
|---|---|
| `routes_stations.py` | Station create/update calls `update_cam2_url()` — already resets counter |
| `routes_system.py` | Quality switch calls `update_cam2_url()` — already resets counter |
| `routes_records.py` | Recording uses direct FFmpeg, not MediaMTX paths |
| `recorder.py` | Not related to live view paths |
| `web-ui/src/App.jsx` | No frontend changes — cam2 disappears from MediaMTX, WebRTC player shows "no signal" naturally |

---

## Behavior Flow

### Case 1: Camera genuinely supports channel=2 (healthy)
```
t=0s:   Station created, cam2 path registered
t=15s:  Monitor loop → cam2 path ready=true → reset counter → OK
t=30s:  Monitor loop → cam2 path ready=true → OK
...     (continues normally, cam2 live view works)
```

### Case 2: Camera doesn't support channel=2 (broken)
```
t=0s:   Station created, cam2 path registered
t=15s:  Monitor loop → cam2 path ready=false → _cam2_fail_count=1
t=30s:  Monitor loop → cam2 path ready=false → _cam2_fail_count=2
        → ≥2 consecutive failures → REMOVE cam2 path
        → Set cam2_url = None (stops re-registration)
        → Log warning
t=45s:  Monitor loop → self.cam2_url is None → skip cam2 check
...     (no more EOF errors, no more retries)
```

### Case 3: Camera temporarily offline then comes back
```
t=0s:   Station created, cam2 path registered
t=15s:  Monitor loop → cam2 path ready=false → _cam2_fail_count=1
t=30s:  Monitor loop → cam2 path ready=true (camera came back) → reset counter → OK
...     (continues normally)
```

### Case 4: Station updated with new cam2 URL
```
update_cam2_url(new_url) → _cam2_fail_count = 0 → fresh start
```

---

## Testing

### Manual test:
1. Create station with mode PIP, IP of a camera that DOES NOT have channel=2
2. Observe MediaMTX logs: EOF on station_X_cam2
3. Wait 30s — cam2 path should be auto-removed
4. Observe: EOF errors stop, no more retries
5. Update station with correct dual-lens camera IP
6. cam2 path re-created, ready=true within 15s

### Edge cases:
- **App restart** with broken cam2: `_cam2_fail_count` starts at 0, takes 30s to detect
- **Quality switch** during detection: `update_cam2_url()` resets counter → fresh start
- **Station delete** during detection: `stop()` removes all paths → clean

### Unit test (optional but recommended):
- Mock MediaMTX API response with `ready=false` → verify `_cam2_fail_count` increments
- After 2 failures → verify `cam2_url` set to None and path removed
- Mock `ready=true` → verify counter resets

---

## Summary

| # | Location | Action |
|---|----------|--------|
| 1 | `CameraStreamManager.__init__` | Add `self._cam2_fail_count = 0` |
| 2 | `CameraStreamManager._monitor_loop` | Replace cam2 re-register logic with health check |
| 3 | `CameraStreamManager.start` | Reset `_cam2_fail_count = 0` |
| 4 | `CameraStreamManager.update_cam2_url` | Reset `_cam2_fail_count = 0` |

Total: **1 file, 4 small changes, ~15 lines added**
