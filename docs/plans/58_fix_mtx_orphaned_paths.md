# Plan 58: Fix MediaMTX Orphaned Paths After Station Deletion

**Ngày**: 2026-04-25
**Mức độ**: Medium — MediaMTX spam error logs vô tận cho station đã xóa
**Loại**: Bug fix (backend)

---

**Status**: Done — PR #75 merged to dev

## Problem

Sau khi xóa station với camera IP không hợp lệ (VD: `192.168.1.99`), MediaMTX vẫn log liên tục:

```
ERR [path station_36] [RTSP source] dial tcp 192.168.1.99:554: i/o timeout
```

MediaMTX path tồn tại mãi vì **không được cleanup đúng cách** khi station bị xóa.

---

## Root Cause Analysis

### Gap 1: Silent failure trong `_mtx_remove_path()` (api.py:171)

```python
except Exception:
    pass  # ← NUỐT lỗi hoàn toàn — connection timeout, MediaMTX down, v.v.
```

Nếu HTTP call đến MediaMTX fail (timeout, network blip), path KHÔNG bị xóa, không log, không retry.

### Gap 2: Cleanup phụ thuộc vào `sm.stop()` (routes_stations.py:127-128)

```python
if sm:
    sm.stop()  # ← CHỈ chạy khi stream_managers có entry cho station_id
```

Nếu `stream_managers.pop(station_id)` trả về `None` (station chưa start, server restart chưa restore), `_mtx_remove_path()` không bao giờ được gọi.

### Gap 3: Không có startup reconciliation (api.py:558-605)

Khi server khởi động, code tạo `CameraStreamManager` cho mỗi station trong DB → register paths. Nhưng **KHÔNG**:
- Query MediaMTX paths hiện có (`GET /v3/paths/list`)
- So sánh với stations trong DB
- Xóa orphaned paths (paths cho stations không còn trong DB)

Nghĩa là orphaned paths từ session trước tồn tại **mãi mãi**.

---

## Scope

### Files to change:

| File | Thay đổi |
|------|----------|
| `api.py` | (1) Fix silent error trong `_mtx_remove_path()`, (2) Thêm `_mtx_cleanup_orphaned_paths()` function, (3) Gọi trong `lifespan()` |
| `routes_stations.py` | (4) Thêm unconditional `_mtx_remove_path()` call trong `delete_station()` |

### Changes chi tiết:

#### 1. Fix `_mtx_remove_path()` error handling (api.py:171)

```python
# BEFORE:
except Exception:
    pass

# AFTER:
except Exception as e:
    logger.warning(f"[MTX] Failed to remove path {name}: {e}")
```

#### 2. Thêm `_mtx_cleanup_orphaned_paths()` function (api.py)

Function mới — gọi sau khi load stations trong `lifespan()`:

```python
def _mtx_cleanup_orphaned_paths(station_ids):
    """Remove MediaMTX paths for stations that no longer exist in DB."""
    import re
    try:
        req = urllib.request.Request(f"{MTX_API}/v3/config/paths/list", method="GET")
        resp = urllib.request.urlopen(req, timeout=5)
        paths = json.loads(resp.read())
        items = paths.get("items", [])
        pattern = re.compile(r"^station_(\d+)(?:_cam2)?$")
        for p in items:
            name = p.get("name", "")
            m = pattern.match(name)
            if m and int(m.group(1)) not in station_ids:
                _mtx_remove_path(int(m.group(1)), suffix=name.removeprefix(f"station_{m.group(1)}"))
                logger.info(f"[MTX] Cleaned orphaned path: {name}")
    except Exception as e:
        logger.debug(f"[MTX] Cleanup scan skipped (MediaMTX not available): {e}")
```

#### 3. Gọi trong `lifespan()` (api.py:605, sau manager.start() loop)

```python
    # ... existing station startup loop ...

    # Cleanup orphaned MediaMTX paths from previous sessions
    station_ids = {st["id"] for st in stations}
    _mtx_cleanup_orphaned_paths(station_ids)
```

#### 4. Unconditional cleanup trong delete handler (routes_stations.py:127-128)

```python
# BEFORE:
if sm:
    sm.stop()

# AFTER:
if sm:
    sm.stop()
# Safety net — luôn cleanup MediaMTX path bất kể sm có tồn tại
api._mtx_remove_path(station_id)
api._mtx_remove_path(station_id, suffix="_cam2")
```

---

## Constraints

- `_mtx_remove_path()` đã handle 404 gracefully → gọi thêm lần nữa không gây side effect
- `_mtx_cleanup_orphaned_paths()` chỉ chạy lúc startup, không ảnh hưởng runtime
- Cleanup scan phải handle gracefully khi MediaMTX không chạy (dev environment)
- Không thay đổi logic của `_mtx_add_path()` hay `_monitor_loop()`

---

## Verification

- [ ] Xóa station → MediaMTX path bị remove (check `GET /v3/paths/list`)
- [ ] Xóa station khi MediaMTX down → restart server → orphaned path bị cleanup lúc startup
- [ ] `_mtx_remove_path()` fail → log warning, không silent
- [ ] `pytest tests/ -v` pass
- [ ] Không regression — station CRUD vẫn hoạt động bình thường
