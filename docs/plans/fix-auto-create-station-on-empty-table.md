# Plan: Fix Auto-Create Station When Table Is Empty

## Problem

**Severity**: High — data integrity bug

After user deletes ALL stations and restarts the system, `init_db()` automatically recreates a station from stale `system_settings` (IP_CAMERA, SAFETY_CODE, RECORD_MODE). This causes:

1. Ghost station appears on UI after restart
2. MediaMTX tries to connect to an offline/incorrect camera IP
3. Continuous RTSP error spam in logs (`dial tcp 192.168.5.114:554: connect: host is down`)
4. WebRTC sessions fail (`no stream is available on path 'station_4'`)
5. User confusion — deleted stations should stay deleted

## Root Cause

**File**: `database.py`, lines 211-232

```python
# Migrate old settings to station 1 if stations table is empty
cursor.execute("SELECT COUNT(*) FROM stations")
if cursor.fetchone()[0] == 0:
    cursor.execute("SELECT config_value FROM system_settings WHERE config_key = 'IP_CAMERA'")
    # ... reads old config ...
    cursor.execute(
        "INSERT INTO stations (name, ip_camera_1, ip_camera_2, safety_code, camera_mode, camera_brand) VALUES ('Bàn Chốt Đơn 1', ...)"
    )
```

This migration code was designed to run ONCE (migrate from single-station v1 to multi-station v2). But it runs every time the `stations` table is empty — including after a user intentionally deletes all stations.

## Fix

### Strategy

Add a `stations_migrated` flag in `system_settings`. Only run the migration when the flag is NOT present. Once migration completes, set the flag. This ensures:

- First-time users: migration runs, station created from old config ✅
- After user deletes all stations: migration skipped, no ghost station ✅
- Existing deployments with stations: migration already irrelevant (stations exist) ✅

### Implementation Steps

#### Step 1: Add migration guard in `database.py` `init_db()`

**File**: `database.py`, around line 211

**Before**:
```python
# Migrate old settings to station 1 if stations table is empty
cursor.execute("SELECT COUNT(*) FROM stations")
if cursor.fetchone()[0] == 0:
    cursor.execute("SELECT config_value FROM system_settings WHERE config_key = 'IP_CAMERA'")
    ip_row = cursor.fetchone()
    ip1 = ip_row[0] if ip_row else ""
    # ... rest of migration ...
    cursor.execute(
        "INSERT INTO stations (name, ip_camera_1, ip_camera_2, safety_code, camera_mode, camera_brand) VALUES ('Bàn Chốt Đơn 1', ?, '', ?, ?, 'imou')",
        (ip1, code, mode),
    )
```

**After**:
```python
# One-time migration: import old single-station settings into stations table
# Guard: only run once, even if stations table is empty later (e.g. user deleted all)
cursor.execute("SELECT config_value FROM system_settings WHERE config_key = 'stations_migrated'")
if not cursor.fetchone():
    cursor.execute("SELECT COUNT(*) FROM stations")
    if cursor.fetchone()[0] == 0:
        cursor.execute("SELECT config_value FROM system_settings WHERE config_key = 'IP_CAMERA'")
        ip_row = cursor.fetchone()
        ip1 = ip_row[0] if ip_row else ""
        # ... rest of migration unchanged ...
        cursor.execute(
            "INSERT INTO stations (name, ip_camera_1, ip_camera_2, safety_code, camera_mode, camera_brand) VALUES ('Bàn Chốt Đơn 1', ?, '', ?, ?, 'imou')",
            (ip1, code, mode),
        )
    # Mark migration as done (regardless of whether station was created)
    cursor.execute(
        "INSERT OR REPLACE INTO system_settings (config_key, config_value) VALUES ('stations_migrated', '1')"
    )
```

**Key change**: The entire migration block is wrapped in `if not cursor.fetchone()` (stations_migrated flag check). The flag is set AFTER the migration attempt, regardless of whether a station was actually created.

#### Step 2: Add test

**File**: `tests/test_database.py` (or `tests/test_database_edge_cases.py`)

Add a test that verifies:
1. After deleting all stations and re-running `init_db()`, no new station is created
2. The migration still works on first run (no `stations_migrated` flag)

```python
def test_no_ghost_station_after_delete_all(self, tmp_path):
    """Deleting all stations then re-initing DB should NOT auto-create a station."""
    monkeypatch.setattr(database, "DB_FILE", str(tmp_path / "test.db"))
    database._init_done = False

    # First init — migration runs, but no old settings → no station created
    database.init_db()
    assert database.get_stations() == [] or len(database.get_stations()) == 0

    # Create a station manually
    sid = database.create_station("Test Station", "192.168.1.100", "", "code123")
    assert len(database.get_stations()) == 1

    # Delete all stations
    database.delete_station(sid)
    assert len(database.get_stations()) == 0

    # Re-init — should NOT create a ghost station
    database._init_done = False
    database.init_db()
    assert len(database.get_stations()) == 0, "Ghost station appeared after re-init!"
```

#### Step 3: Verify manually

1. Delete all stations via UI
2. Stop system
3. Start system
4. Verify: UI shows empty station list, no `station_*` in MediaMTX logs
5. Verify: `system_settings` table has `stations_migrated = 1`

## Files to Change

| File | Change |
|------|--------|
| `database.py` | Add `stations_migrated` guard around migration logic |
| `tests/test_database.py` | Add `test_no_ghost_station_after_delete_all` |

## Acceptance Criteria

- [ ] After deleting all stations and restarting, no ghost station appears
- [ ] First-time migration still works (create station from old system_settings)
- [ ] New test passes: `test_no_ghost_station_after_delete_all`
- [ ] Existing tests still pass: `pytest tests/ -v`
- [ ] No RTSP error spam in logs after restart with empty station list
- [ ] `system_settings` table contains `stations_migrated = 1` after first init

## Risk

**Low**. The change only adds a guard flag. The migration logic itself is unchanged. Existing deployments with stations are unaffected (stations table is not empty, migration is already irrelevant).
