# Plan: Auto-migrate deprecated _sim camera modes

**Status**: DONE — Implemented and merged.

**Ngay**: 2026-04-22
**Muc do**: Low — Cleanup, silent fallback → explicit migration
**Loai**: Data migration + logging
**Trigger**: PR #32 removed _sim modes from UI/backend, but DB may still have old values

---

## Background

PR #32 removed `pip_sim` and `dual_file_sim` from:
- UI dropdown (SetupModal.jsx)
- Backend mode mapping (routes_records.py)
- Camera mode descriptions

However, stations **already in the database** with `camera_mode = "pip_sim"` or `"dual_file_sim"` will silently fallback to SINGLE mode in `routes_records.py` — no warning, no migration. Admin won't know their station is operating in degraded mode.

---

## Scope

**2 files to change:**

| # | File | Change |
|---|------|--------|
| 1 | `api.py` | Auto-migrate deprecated modes in lifespan init |
| 2 | `database.py` | Add `update_station_camera_mode()` helper |

---

## Changes

### 1. `database.py` — Add `update_station_camera_mode()`

Add a new function to update only the `camera_mode` field of a station:

```python
def update_station_camera_mode(station_id, new_mode):
    """Update only the camera_mode field for a station."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE stations SET camera_mode = ? WHERE id = ?",
            (new_mode, station_id),
        )
        conn.commit()
```

**Why a new function?** `update_station()` requires ALL fields (name, ip_camera_1, ip_camera_2, etc.). We only want to change 1 field — a targeted update avoids needing to fetch and re-pass all other fields.

### 2. `api.py` — Auto-migrate in lifespan init (line ~546)

**Before:**
```python
cam2_ip = st.get("ip_camera_2", "").strip()
mode = st.get("camera_mode", "SINGLE").upper()
if cam2_ip:
```

**After:**
```python
cam2_ip = st.get("ip_camera_2", "").strip()
mode = st.get("camera_mode", "SINGLE").upper()
# Auto-migrate deprecated camera modes
if mode in ("PIP_SIM", "DUAL_FILE_SIM"):
    migrated = "PIP" if mode == "PIP_SIM" else "DUAL_FILE"
    logger.warning(
        "Station %d has deprecated camera_mode '%s'. "
        "Auto-migrated to '%s'.",
        st["id"], mode, migrated,
    )
    database.update_station_camera_mode(st["id"], migrated)
    mode = migrated
if cam2_ip:
```

**Why in lifespan init?** This runs once on server start. It's the natural place for one-time migrations — every station is loaded and initialized here.

### 3. `routes_records.py` — Add warning log for deprecated mode (line ~160)

**Before:**
```python
url1 = api.get_rtsp_url(ip1, code, channel=1, brand=brand)
if c_mode == "dual_file" or c_mode == "pip":
```

**After:**
```python
url1 = api.get_rtsp_url(ip1, code, channel=1, brand=brand)
# Log warning for deprecated modes (should be migrated by lifespan init)
if c_mode in ("pip_sim", "dual_file_sim"):
    logger.warning(
        "Station %d still uses deprecated mode '%s'. "
        "Should have been auto-migrated on server start.",
        sid, c_mode,
    )
    c_mode = "pip" if c_mode == "pip_sim" else "dual_file"
if c_mode == "dual_file" or c_mode == "pip":
```

**Why both places?** Lifespan init catches it on restart. But if a station is created or updated with a deprecated mode after startup (e.g., via API call with old value), this is the safety net.

---

## Test Cases

1. **Station with `camera_mode = "pip_sim"` in DB** → Server start → auto-migrated to `"pip"`, DB updated, log warning emitted
2. **Station with `camera_mode = "dual_file_sim"` in DB** → Server start → auto-migrated to `"dual_file"`, DB updated
3. **Station with `camera_mode = "pip"`** → No migration, no warning
4. **Station with `camera_mode = "SINGLE"`** → No change
5. **`routes_records.py` receives deprecated mode** → Log warning, treat as parent mode
6. **`pytest tests/ -q`** passes
7. **Second server restart** → No warning for already-migrated stations

---

## Migration Behavior

| Old Mode | New Mode | cam2_url | Recording Mode |
|----------|----------|----------|----------------|
| `pip_sim` | `pip` | Generated from ip_camera_1 channel=2 | PIP (FFmpeg split if same URL) |
| `dual_file_sim` | `dual_file` | Generated from ip_camera_1 channel=2 | DUAL_FILE (2 files, same content if 1 camera) |

**Note**: If the camera is single-lens (no channel 2), `pip`/`dual_file` will attempt channel 2 → may fail. But this was the same behavior as before the _sim removal — recorder.py has fallback: `self.rtsp_url_2 = rtsp_url_2 if rtsp_url_2 else rtsp_url_1`.

---

## NOT Changed

- `routes_stations.py` — `_resolve_cam2_url` already only checks `pip`/`dual_file`
- `SetupModal.jsx` — Already doesn't show _sim options
- `recorder.py` — Uses record_mode (SINGLE/PIP/DUAL_FILE), not camera_mode
- Database schema — No change needed, `camera_mode` is TEXT
