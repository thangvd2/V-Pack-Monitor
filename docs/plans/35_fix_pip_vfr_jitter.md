# Fix: PIP Playback Jitter — Variable Frame Rate Root Cause

**Status**: DONE — Implemented and merged.

## Problem

Video PIP playback bị giật sau khi fix encoder/bitrate (PR #45). Tốc độ xử lý (scan→stop) nhanh, nhưng file MP4 kết quả playback bị lag.

## Root Cause — Dữ liệu thực tế

Phân tích file PIP thực tế bằng ffprobe:

```
File: 2602285208_20260422_230449_PIP.mp4 (21 MB, 51s)
Resolution: 2880x1620
Claimed FPS: 15fps
Actual avg FPS: 2.26fps
Total frames: 115 (should be 766 at 15fps)
Frame drop rate: 85%

Frame timing:
  Frame 20: pts=1.464  dur=0.067  ← bình thường
  Frame 21: pts=1.530  dur=0.374  ← gap gấp 5.6x
  Frame 22: pts=1.905  dur=1.867  ← gap gấp 28x (MASSIVE drop)
  Frame 23: pts=3.772  dur=0.067  ← nhảy cóc 2 giây

Jitter: 3184% so với expected interval
```

**FFmpeg không kịp xử lý real-time → drop 85% frames → VFR output → browser jitter.**

### 5 nguyên nhân xếp theo mức độ ảnh hưởng:

| # | Nguyên nhân | Mức độ | Giải thích |
|---|------------|--------|------------|
| 1 | **`-use_wallclock_as_timestamps 1`** | CRITICAL | Thay PTS gốc bằng system clock → bake network jitter vào timestamps. FFmpeg docs và Frigate NVR project confirm flag này gây stutter với filter_complex. |
| 2 | **Không có `-fps_mode cfr`** | CRITICAL | Không ép constant frame rate → output VFR → browser decode jitter |
| 3 | **Thiếu `setpts=PTS-STARTPTS`** trong filter_complex | HIGH | 2 RTSP inputs có PTS gốc khác nhau (khác session) → overlay filter sync sai → wait/drop frames |
| 4 | **Không có `-thread_queue_size`** cho RTSP inputs | MODERATE | Input buffer quá nhỏ → overflow → frame drop khi overlay filter chậm |
| 5 | **Post-processing thiếu `-fflags +genpts+igndts`** | MODERATE | Timestamp errors từ MPEG-TS carried sang MP4 |

## Fix Plan — 6 thay đổi trong `recorder.py`

### Change 1: Bỏ `-use_wallclock_as_timestamps` — thay bằng `setpts` trong filter_complex

**Vì sao:** `-use_wallclock_as_timestamps 1` phá vỡ PTS ordering mà overlay filter dùng để sync. FFmpeg overlay docs khuyến nghị dùng `setpts=PTS-STARTPTS` để reset PTS mỗi input về 0.

**Dual-input branch** (line 294-317):

Before:
```python
"-use_wallclock_as_timestamps", "1",
"-rtsp_transport", "tcp", "-i", self.rtsp_url_1,
"-use_wallclock_as_timestamps", "1",
"-rtsp_transport", "tcp", "-i", self.rtsp_url_2,
"-filter_complex",
"[1:v]scale=iw/3:-1[pip]; [0:v][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10",
```

After:
```python
"-rtsp_transport", "tcp", "-i", self.rtsp_url_1,
"-rtsp_transport", "tcp", "-i", self.rtsp_url_2,
"-filter_complex",
"[0:v]setpts=PTS-STARTPTS[main]; [1:v]setpts=PTS-STARTPTS,scale=iw/3:-1[pip]; [main][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10",
```

**Same-URL branch** (line 270-289):

Before:
```python
"-filter_complex",
"[0:v]split=2[main][pip_raw]; [pip_raw]scale=iw/3:-1[pip]; [main][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10",
```

After:
```python
"-filter_complex",
"[0:v]split=2[main][pip_raw]; [pip_raw]scale=iw/3:-1[pip]; [main][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10, setpts=PTS-STARTPTS[out]",
```

Note: Same-URL branch không cần `setpts` cho từng input (chỉ có 1 input), nhưng thêm `setpts=PTS-STARTPTS` sau overlay để normalize output timestamps.

### Change 2: Thêm `-fps_mode cfr` + `-r 15` trước output

Ép constant frame rate. FFmpeg sẽ dup/drop frames để duy trì 15fps output.

Thêm vào cả 2 PIP branches, **SAU** `*_build_pip_encode_args(encoder)` và **TRƯỚC** `"-c:a", "aac"`:

```python
*_build_pip_encode_args(encoder),
"-fps_mode", "cfr",
"-r", "15",
"-c:a", "aac",
```

Note: Dùng `-fps_mode cfr` (FFmpeg >= 5.1) thay vì deprecated `-vsync cfr`. Nếu FFmpeg version cũ không hỗ trợ, fallback sang `-vsync cfr`.

### Change 3: Thêm `-thread_queue_size 512` cho mỗi RTSP input

Tăng input buffer để overlay filter không bị starved khi decode chậm.

**Dual-input branch** — thêm trước mỗi `-rtsp_transport`:
```python
"-thread_queue_size", "512",
"-rtsp_transport", "tcp", "-i", self.rtsp_url_1,
"-thread_queue_size", "512",
"-rtsp_transport", "tcp", "-i", self.rtsp_url_2,
```

**Same-URL branch** — thêm trước `-rtsp_transport`:
```python
"-thread_queue_size", "512",
"-rtsp_transport", "tcp", "-i", self.rtsp_url_1,
```

### Change 4: Thêm `-fflags +genpts+discardcorrupt` cho RTSP inputs

Generate PTS nếu thiếu (RTSP network glitch) và discard corrupt packets thay vì propagate lỗi.

Thêm vào **đầu** command (sau `"ffmpeg", "-y"`) cho cả 2 branches:
```python
command = ["ffmpeg", "-y", "-fflags", "+genpts+discardcorrupt"]
```

### Change 5: Thêm `-pix_fmt yuv420p` cho libx264 trong `_build_pip_encode_args()`

**File:** `recorder.py` line 106-113

Before:
```python
if encoder == "libx264":
    return [
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-threads", "0",
    ]
```

After:
```python
if encoder == "libx264":
    return [
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-threads", "0",
    ]
```

### Change 6: Sửa post-processing TS→MP4 remux

**File:** `recorder.py` line 389-399

Before:
```python
cmd = [
    _ffmpeg_bin("ffmpeg"),
    "-y",
    "-i", ts_path,
    "-c", "copy",
    "-movflags", "+faststart",
    final_path,
]
```

After:
```python
cmd = [
    _ffmpeg_bin("ffmpeg"),
    "-y",
    "-fflags", "+igndts",
    "-i", ts_path,
    "-c", "copy",
    "-fflags", "+genpts",
    "-movflags", "+faststart",
    final_path,
]
```

`-fflags +igndts` (input): Ignore DTS errors khi đọc MPEG-TS
`-fflags +genpts` (output): Generate PTS mới để đảm bảo timestamps clean trong MP4

## Implementation Steps

1. **Update `_build_pip_encode_args()`** — thêm `-pix_fmt yuv420p` cho libx264
2. **Update same-URL PIP branch** (line 270-289):
   - Thêm `-fflags +genpts+discardcorrupt` đầu command
   - Thêm `-thread_queue_size 512` trước input
   - Sửa filter_complex thêm `setpts=PTS-STARTPTS`
   - Thêm `-fps_mode cfr -r 15`
3. **Update dual-input PIP branch** (line 290-317):
   - Thêm `-fflags +genpts+discardcorrupt` đầu command
   - Bỏ `-use_wallclock_as_timestamps 1`
   - Thêm `-thread_queue_size 512` trước mỗi input
   - Sửa filter_complex thêm `setpts=PTS-STARTPTS` cho cả 2 inputs
   - Thêm `-fps_mode cfr -r 15`
4. **Update post-processing** (line 389-399): thêm `-fflags +igndts` và `-fflags +genpts`
5. **Test**: Record PIP 10-15s, verify bằng ffprobe: `avg_frame_rate` phải ổn định 15fps, không VFR

## Files to Change

| File | Thay đổi |
|------|----------|
| `recorder.py` | Tất cả thay đổi |

## Files to NOT Change

- `api.py` — Không đổi
- `database.py` — Không đổi
- `web-ui/` — Không đổi frontend
- `_detect_hw_encoder()` — Không sửa
- `_build_transcode_cmd()` — Không sửa (HEVC transcode không liên quan PIP)
- `_is_hevc()` — Không sửa
- SINGLE mode (line 188-212) — Không chạm, dùng `-c:v copy`
- DUAL_FILE mode (line 214-261) — Không chạm, dùng `-c:v copy`
- `stop_recording()` logic (line 339-374) — Không chạm (graceful stop, process wait, cleanup)
- Chỉ sửa `stop_recording()` post-processing remux command (line 389-399)

## Cross-Platform Impact

| Thay đổi | macOS | Windows | Linux |
|----------|-------|---------|-------|
| Bỏ `-use_wallclock_as_timestamps` | ✅ Tốt hơn | ✅ Tốt hơn | ✅ Tốt hơn |
| `-fps_mode cfr` | ✅ FFmpeg >= 5.1 hỗ trợ | ✅ FFmpeg >= 5.1 | ✅ |
| `-thread_queue_size 512` | ✅ | ✅ | ✅ |
| `-fflags +genpts+igndts` | ✅ | ✅ | ✅ |
| `-pix_fmt yuv420p` | ✅ | ✅ | ✅ |
| `setpts=PTS-STARTPTS` | ✅ Standard filter | ✅ | ✅ |

**Không regression.** Tất cả tham số là FFmpeg standard, hoạt động trên mọi platform.

## Testing

### Test 1: PIP Recording Quality
1. Station PIP mode, record 10-15 giây
2. Stop recording
3. Verify bằng ffprobe:
   ```
   ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate,avg_frame_rate,nb_frames -of csv=p=0 output.mp4
   ```
4. **Expected**: `avg_frame_rate` = `r_frame_rate` = 15/1 (hoặc gần bằng), nb_frames ≈ duration × 15
5. Playback trong browser → mượt, không giật

### Test 2: Frame Timestamp Analysis
```
ffprobe -v error -select_streams v:0 -show_entries frame=pts_time,duration_time -of json -read_intervals '%+#30' output.mp4
```
**Expected**: Mọi `duration_time` ≈ 0.0667 (1/15s), không có gap lớn

### Test 3: Non-PIP Regression
1. Quay SINGLE mode → playback mượt
2. Quay DUAL_FILE mode → playback mượt

## Risk Assessment

- **Risk: THẤP-TRUNG BÌNH** — Thay đổi FFmpeg command structure, nhưng:
  - Tất cả tham số là FFmpeg standard, documented
  - Chỉ ảnh hưởng PIP mode
  - SINGLE và DUAL_FILE dùng `-c:v copy`, hoàn toàn không đổi
  - Nếu `-fps_mode cfr` không được hỗ trợ (FFmpeg cũ), fallback: `-vsync cfr`

### Fallback Plan
Nếu sau fix vẫn jitter (do hardware encode không kịp real-time):
- Option A: Giảm resolution input (dùng sub-stream 640x480 cho PIP thay vì main-stream 2880x1620)
- Option B: Record DUAL_FILE riêng + composite ở post-processing (không real-time)
- Option C: Thêm `-g 30` (keyframe mỗi 2s) để cải thiện seek performance
