# Fix: Log Station Name Alongside Station ID

## Problem

Khi debug production, logs chỉ hiển thị `station_{id}` mà không có station name. Sau khi tạo/xóa nhiều stations, ID tăng lên (5, 6, 7...) và không map được với tên hiển thị trên UI ("số 1", "số 2"...).

### Ví dụ log hiện tại:

```
# MediaMTX — chỉ có ID, không có name
[path station_5] [RTSP source] started
[path station_5_cam2] stream is available and online

# Recorder — KHÔNG CÓ station info
Bat dau ghi hinh (PIP) Don hang: 6976391034952
GPU encoder detected: h264_videotoolbox
Dang dung ghi hinh va dong goi video...

# API — chỉ có ID
[MTX] station_5_cam2 failed health check 2x
[MTX] monitor loop error for station_5: ...
```

### Log mong muốn:

```
# MediaMTX — thêm station name
[path station_5 "số 1"] [RTSP source] started
[path station_5_cam2 "số 1"] stream is available and online

# Recorder — có station name
[số 1] Bat dau ghi hinh (PIP) Don hang: 6976391034952
[số 1] GPU encoder detected: h264_videotoolbox
[số 1] Dang dung ghi hinh va dong goi video...

# API — có station name
[MTX] station_5 "số 1" cam2 failed health check 2x
[MTX] monitor loop error for station_5 "số 1": ...
```

## Fix Approach

Pass `station_name` vào `CameraRecorder` và `CameraStreamManager` khi khởi tạo. Log kèm name ở mọi nơi.

### Change 1: Thêm `station_name` vào `CameraRecorder`

**File:** `recorder.py`

**Constructor** (line 156):
```python
# Before
def __init__(self, rtsp_url_1, rtsp_url_2=None, output_dir="recordings", record_mode="SINGLE"):

# After
def __init__(self, rtsp_url_1, rtsp_url_2=None, output_dir="recordings", record_mode="SINGLE", station_name=""):
    ...
    self.station_name = station_name
```

**Log lines** — thêm station name prefix:

Line 332:
```python
# Before
logger.info(f"Bat dau ghi hinh ({self.record_mode}) Don hang: {waybill_code}")

# After
tag = f"[{self.station_name or 'Unknown'}] " if self.station_name else ""
logger.info(f"{tag}Bat dau ghi hinh ({self.record_mode}) Don hang: {waybill_code}")
```

Line 357:
```python
# Before
logger.info("Dang dung ghi hinh va dong goi video...")

# After
logger.info(f"{tag}Dang dung ghi hinh va dong goi video...")
```

### Change 2: Pass `station_name` khi tạo `CameraRecorder` trong `routes_records.py`

**File:** `routes_records.py`, line 183

```python
# Before
new_recorder = CameraRecorder(url1, rtsp_url_2=url2, record_mode=r_mode)

# After
station = database.get_station(sid)
new_recorder = CameraRecorder(url1, rtsp_url_2=url2, record_mode=r_mode, station_name=station["name"] if station else "")
```

### Change 3: Thêm `station_name` vào `CameraStreamManager`

**File:** `api.py`, class `CameraStreamManager`

**Constructor** (line 170):
```python
# Before
def __init__(self, url, station_id=None, cam2_url=None):

# After
def __init__(self, url, station_id=None, cam2_url=None, station_name=""):
    ...
    self.station_name = station_name
```

**Log lines** — thêm station name:

Line 265-267:
```python
# Before
logger.warning(
    f"[MTX] station_{self.station_id}_cam2 failed health check "
    f"{self._cam2_fail_count}x — removing broken cam2 path"
)

# After
tag = f'"{self.station_name}"' if self.station_name else ""
logger.warning(
    f"[MTX] station_{self.station_id} {tag} cam2 failed health check "
    f"{self._cam2_fail_count}x — removing broken cam2 path"
)
```

Line 274:
```python
# Before
logger.error(f"[MTX] monitor loop error for station_{self.station_id}: {e}")

# After
logger.error(f"[MTX] monitor loop error for station_{self.station_id} {tag}: {e}")
```

### Change 4: Pass `station_name` khi tạo `CameraStreamManager`

**File:** `api.py`, `lifespan()` line 585:

```python
# Before
manager = CameraStreamManager(live_url, station_id=st["id"], cam2_url=cam2_url)

# After
manager = CameraStreamManager(live_url, station_id=st["id"], cam2_url=cam2_url, station_name=st.get("name", ""))
```

**File:** `routes_stations.py`, line 88:

```python
# Before
sm = api.CameraStreamManager(url, station_id=new_id, cam2_url=cam2_url)

# After
sm = api.CameraStreamManager(url, station_id=new_id, cam2_url=cam2_url, station_name=data.get("name", ""))
```

### Change 5: `_mtx_add_path` / `_mtx_remove_path` — log station name

**File:** `api.py`

`_mtx_add_path` (line 114):
```python
# Before
def _mtx_add_path(station_id, rtsp_url, suffix=""):
    name = f"station_{station_id}{suffix}"

# After
def _mtx_add_path(station_id, rtsp_url, suffix="", station_name=""):
    name = f"station_{station_id}{suffix}"
```

Thêm log info khi register thành công:
```python
urllib.request.urlopen(req, timeout=5)
tag = f' "{station_name}"' if station_name else ""
logger.info(f"[MTX] Registered path {name}{tag}")
return
```

Tương tự cho `_mtx_remove_path` — thêm station_name param + log.

Update callers để pass `station_name=self.station_name` từ `CameraStreamManager`.

## Implementation Steps

1. Update `CameraRecorder.__init__()` — thêm `station_name` param
2. Update `CameraRecorder` log lines — thêm station name prefix
3. Update `routes_records.py` — pass `station_name` khi tạo `CameraRecorder`
4. Update `CameraStreamManager.__init__()` — thêm `station_name` param
5. Update `CameraStreamManager` log lines — thêm station name
6. Update `_mtx_add_path()` / `_mtx_remove_path()` — thêm `station_name` param + log
7. Update `lifespan()` — pass `station_name` khi tạo `CameraStreamManager` và `_mtx_add_path`
8. Update `routes_stations.py` — pass `station_name` khi tạo `CameraStreamManager`
9. Update tests — thêm `station_name` param cho `CameraRecorder` constructor

## Files to Change

| File | Thay đổi |
|------|----------|
| `recorder.py` | Thêm `station_name` param, update log lines |
| `api.py` | `CameraStreamManager`, `_mtx_add_path`, `_mtx_remove_path`, `lifespan()` |
| `routes_records.py` | Pass `station_name` khi tạo `CameraRecorder` |
| `routes_stations.py` | Pass `station_name` khi tạo `CameraStreamManager` |
| `tests/test_recorder.py` | Update `CameraRecorder()` calls (không cần pass `station_name` vì default="" ) |

## Files to NOT Change

- `database.py` — Không đổi
- `web-ui/` — Không đổi frontend
- MediaMTX config — Không đổi (MediaMTX log format không control được, chỉ improve app-side logs)
- SINGLE/DUAL_FILE/PIP recording logic — Không đổi logic, chỉ thêm param
- `_detect_hw_encoder()`, `_build_pip_encode_args()`, `_build_transcode_cmd()` — Không sửa

## Testing

### Test 1: Log hiển thị station name
1. Restart hệ thống
2. Kiểm log startup — phải thấy `[MTX] Registered path station_5 "số 1"`
3. Scan barcode để record
4. Kiểm log recorder — phải thấy `[số 1] Bat dau ghi hinh (PIP) Don hang: xxx`

### Test 2: Station không có name (edge case)
1. Nếu `station_name=""` → log không có tag, format cũ: `Bat dau ghi hinh (PIP) Don hang: xxx`
2. Backward compatible

### Test 3: Existing tests still pass
- `CameraRecorder()` constructor có default `station_name=""` → tests hiện tại không bị break
- Chạy `pytest tests/ -q` → 324 passed

## Risk Assessment

- **Risk: RẤT THẤP** — Chỉ thêm optional param + thay đổi log string format
- Không thay đổi business logic
- `station_name` có default value `""` → backward compatible
- Tests hiện tại không cần sửa vì default value
