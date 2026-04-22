# Plan: Fix Download Filename + Add Duration Display

## Goal
1. Download filename phải giống tên gốc hiển thị trên UI (hiện đang bị ghi đè thành `video_42_0.mp4`)
2. Hiển thị thời lượng video trong danh sách lịch sử ghi hình (hiện chỉ có ngày/giờ)

---

## Item 1: Fix Download Filename

### Root Cause
`VideoPlayerModal.jsx` line 288 — fetch video as blob, set `a.download = video_${record_id}_${file_index}.mp4` (generic). Bỏ qua tên gốc và `waybillCode` prop.

### Fix: `web-ui/src/VideoPlayerModal.jsx`

**Line 288** — Extract filename from `Content-Disposition` header (backend đã trả đúng tên gốc):

```jsx
// BEFORE
a.download = `video_${match[1]}_${match[2]}.mp4`;

// AFTER — parse filename from Content-Disposition header
const disposition = response.headers.get('Content-Disposition');
let downloadName = `${waybillCode || 'video'}.mp4`;
if (disposition) {
  const matchFilename = disposition.match(/filename\*?=(?:UTF-8''|"?)([^";]+)/i);
  if (matchFilename) downloadName = decodeURIComponent(matchFilename[1].replace(/"/g, ''));
}
a.download = downloadName;
```

Logic:
1. Backend `routes_records.py` đã set `Content-Disposition: attachment; filename="SPX12345_20260423_143022.mp4"` ✅
2. Frontend parse header → lấy `SPX12345_20260423_143022.mp4`
3. Fallback: dùng `waybillCode.mp4` nếu header không parse được

### Files Changed
- `web-ui/src/VideoPlayerModal.jsx` — line 288

---

## Item 2: Add Duration Display

### Current State
- **DB**: `packing_video` table không có cột `duration`
- **video_worker.py `_verify_video()`**: Đã extract duration qua ffprobe nhưng chỉ dùng bool check → **vứt giá trị float đi**
- **API response**: Không có field `duration`
- **Frontend**: Chỉ hiển thị `recorded_at`, không có thời lượng

### Changes

#### 2A. DB Schema: `database.py`

**Lines 162-173** — Thêm `duration REAL` vào CREATE TABLE:
```sql
CREATE TABLE IF NOT EXISTS packing_video (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    station_id INTEGER DEFAULT 1,
    waybill_code TEXT NOT NULL,
    video_paths TEXT NOT NULL,
    record_mode TEXT NOT NULL,
    recorded_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'READY' CHECK(status IN ('READY', 'RECORDING', 'PROCESSING', 'FAILED', 'SYNCED')),
    is_synced INTEGER DEFAULT 0,
    duration REAL DEFAULT 0
)
```

**Lines 175-184** — Migration (ALTER TABLE):
```python
if "duration" not in columns:
    cursor.execute("ALTER TABLE packing_video ADD COLUMN duration REAL DEFAULT 0;")
```

#### 2B. video_worker.py: Return duration from _verify_video

**Rename `_verify_video` → `_get_video_info`** — return tuple `(is_valid, duration)`:

```python
def _get_video_info(filepath):
    """Verify video file and return (is_valid, duration_seconds)."""
    if not filepath or not os.path.exists(filepath):
        return (False, 0)
    if os.path.getsize(filepath) == 0:
        return (False, 0)
    try:
        cmd = [
            recorder._ffmpeg_bin("ffprobe"),
            "-v", "error",
            "-show_entries", "format=duration",
            "-of", "csv=p=0",
            filepath,
        ]
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        duration_str = r.stdout.strip()
        if duration_str:
            duration = float(duration_str)
            if duration > 0:
                return (True, duration)
    except Exception:
        pass
    return (False, 0)
```

#### 2C. video_worker.py: Save duration in _process_stop_and_save

**Lines 104-122** — Extract duration from first valid file, store in DB:

```python
# BEFORE
all_valid = True
for f in saved_files:
    if not _verify_video(f):
        all_valid = False
        break

if all_valid:
    database.update_record_status(record_id, "READY", video_paths=saved_files)
else:
    database.update_record_status(record_id, "FAILED", video_paths=saved_files)

# AFTER
all_valid = True
total_duration = 0.0
for f in saved_files:
    is_valid, file_duration = _get_video_info(f)
    if not is_valid:
        all_valid = False
        break
    # Use longest file as representative duration (PIP may have different lengths)
    total_duration = max(total_duration, file_duration)

if all_valid:
    database.update_record_status(record_id, "READY", video_paths=saved_files, duration=total_duration)
else:
    database.update_record_status(record_id, "FAILED", video_paths=saved_files)
```

#### 2D. database.py: Update update_record_status to accept duration

**Line 498** — Add `duration` parameter:

```python
def update_record_status(record_id, status, video_paths=None, duration=None):
    # H2: Validate status before update
    if status not in _VALID_RECORD_STATUSES:
        raise ValueError(f"Invalid record status: {status}. Must be one of {_VALID_RECORD_STATUSES}")
    with get_connection() as conn:
        cursor = conn.cursor()
        if video_paths is not None:
            paths_str = ",".join(video_paths) if isinstance(video_paths, list) else video_paths
            if duration is not None:
                cursor.execute(
                    "UPDATE packing_video SET status = ?, video_paths = ?, duration = ? WHERE id = ?",
                    (status, paths_str, duration, record_id),
                )
            else:
                cursor.execute(
                    "UPDATE packing_video SET status = ?, video_paths = ? WHERE id = ?",
                    (status, paths_str, record_id),
                )
        else:
            if duration is not None:
                cursor.execute(
                    "UPDATE packing_video SET status = ?, duration = ? WHERE id = ?",
                    (status, duration, record_id),
                )
            else:
                cursor.execute(
                    "UPDATE packing_video SET status = ? WHERE id = ?",
                    (status, record_id),
                )
        conn.commit()
```

#### 2E. database.py: Add duration to get_records_v2

**Line 566** — Add `p.duration` to SELECT:
```python
base_select = "p.id, p.waybill_code, p.video_paths, p.record_mode, datetime(p.recorded_at, 'localtime') AS recorded_at, s.name, p.status, p.duration"
```

**Lines 671-681** — Add duration to response dict:
```python
records.append({
    "id": r[0],
    "waybill_code": r[1],
    "video_paths": paths,
    "record_mode": r[3],
    "recorded_at": r[4],
    "station_name": r[5],
    "status": r[6],
    "duration": r[7] if len(r) > 7 else 0,  # NEW
})
```

#### 2F. Frontend: Display duration in record card

**App.jsx line 2008-2010** — Add duration next to date:

```jsx
// BEFORE
<p className="text-xs text-slate-400 mb-3 md:mb-4 font-mono">
  {new Date(record.recorded_at).toLocaleString('vi-VN')}
</p>

// AFTER
<div className="flex items-center gap-3 mb-3 md:mb-4 text-xs text-slate-400 font-mono">
  <span>{new Date(record.recorded_at).toLocaleString('vi-VN')}</span>
  {record.duration > 0 && (
    <span className="px-2 py-0.5 bg-white/5 rounded text-emerald-400 border border-emerald-500/20">
      ⏱ {Math.floor(record.duration / 60)}:{Math.floor(record.duration % 60).toString().padStart(2, '0')}
    </span>
  )}
</div>
```

---

## Files Modified

| File | Change |
|------|--------|
| `web-ui/src/VideoPlayerModal.jsx` | Parse Content-Disposition for download filename |
| `video_worker.py` | `_verify_video` → `_get_video_info` returns `(valid, duration)` |
| `database.py` | Schema: add `duration REAL` column + migration |
| `database.py` | `update_record_status()` accept `duration` param |
| `database.py` | `get_records_v2()` include `duration` in SELECT + response |
| `web-ui/src/App.jsx` | Display duration badge in record card |

## Test Plan

1. **Unit test `_get_video_info`**: Mock ffprobe output, verify returns (True, 30.5)
2. **Unit test `update_record_status` with duration**: Verify DB row has duration value
3. **Unit test `get_records_v2`**: Verify response includes `duration` field
4. **Unit test migration**: Verify ALTER TABLE adds `duration` column
5. **Frontend**: Record with known duration → verify badge shows correct `X:XX`
6. **Download**: Click download → verify filename matches UI display name (e.g. `SPX12345_20260423_143022.mp4`)

## Backward Compatibility

- Old records without duration: `duration REAL DEFAULT 0` → frontend checks `record.duration > 0` → hides badge for old records
- `_get_video_info` is internal (only called by `_process_stop_and_save`) → no API break
- `update_record_status` new param `duration=None` → optional, no break for existing callers
