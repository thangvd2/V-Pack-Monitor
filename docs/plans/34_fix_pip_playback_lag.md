# Fix: PIP Mode Playback Lag + Encoder Quality Consistency

**Status**: DONE — Implemented and merged.

## Overview

2 bugs trong `recorder.py`, cùng 1 file, liên quan encoder selection:

1. **PIP mode playback lag** (CAO) — PIP hardcode encoder + bitrate quá thấp → video giật
2. **Post-processing thiếu quality params** (TRUNG BÌNH) — HEVC transcode cho QSV/NVENC/AMF không có quality control → kết quả không đoán trước được

---

## Bug 1: PIP Mode Playback Lag

### Root Cause

PIP mode (line 242-245) hardcode encoder thay vì dùng `_detect_hw_encoder()`:

```python
# recorder.py line 242-245
sys_os = platform.system()
vcodec = "libx264"
if sys_os == "Darwin":
    vcodec = "h264_videotoolbox"
```

Kết hợp với bitrate `2000k` quá thấp (line 260, 292), PIP composite 2 camera bị:
- macOS: GPU encoder đúng nhưng bitrate thấp → chất lượng kém
- Windows: Luôn dùng CPU `libx264` (bỏ qua GPU) + bitrate thấp → chậm + kém

### Fix

**Bước 1**: Thay hardcode bằng `_detect_hw_encoder()`

**Before** (line 242-245):
```python
sys_os = platform.system()
vcodec = "libx264"
if sys_os == "Darwin":
    vcodec = "h264_videotoolbox"
```

**After**:
```python
encoder, hw_accel = _detect_hw_encoder()
```

**Bước 2**: Thêm hàm `_build_pip_encode_args(encoder)` — đặt sau `_build_transcode_cmd()` (sau line 101)

```python
def _build_pip_encode_args(encoder):
    """Build encoding args optimized for PIP composite recording."""
    if encoder == "libx264":
        # CRF adapts quality to content complexity — good for PIP with mixed static/detail areas
        return [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
            "-threads", "0",
        ]
    elif encoder == "h264_videotoolbox":
        # VideoToolbox does not support CRF — use higher bitrate for PIP composite
        return [
            "-c:v", "h264_videotoolbox",
            "-b:v", "6M",
            "-pix_fmt", "yuv420p",
        ]
    else:
        # GPU encoders (h264_qsv, h264_nvenc, h264_amf)
        return [
            "-c:v", encoder,
            "-b:v", "6M",
            "-pix_fmt", "yuv420p",
        ]
```

Tại sao args khác nhau:
- `libx264`: CRF 23 adaptive → frame phức tạp (PIP overlay) được nhiều bits, frame tĩnh ít bits. `ultrafast` giảm CPU load.
- GPU encoders: Không hỗ trợ CRF → dùng `-b:v 6M` (6 Mbps, đủ cho 2 camera composite). `yuv420p` đảm bảo compatibility.
- Bitrate tăng từ `2000k` → `6M`: PIP ghép 2 camera cần nhiều data hơn 2x so với single stream.

**Bước 3**: Update cả 2 PIP branches (same-URL split: line 248-270, dual-input: line 272-302)

Cả 2 branch hiện dùng:
```python
"-c:v", vcodec, "-b:v", "2000k", "-pix_fmt", "yuv420p", "-c:a", "aac",
```

Thay bằng:
```python
*_build_pip_encode_args(encoder), "-c:a", "aac",
```

**Bước 4**: Thêm `hw_accel` flags vào FFmpeg command

Cho dual-input PIP branch (2 camera khác nhau), thêm hw_accel flags:
```python
# Build base command with optional hw_accel
base_cmd = [_ffmpeg_bin("ffmpeg"), "-y"]
if hw_accel:
    base_cmd += hw_accel.split()
# Then append the rest of the command...
```

Cho same-URL split branch, cũng thêm tương tự.

---

## Bug 2: `_build_transcode_cmd()` Thiếu Quality Params cho QSV/NVENC/AMF

### Root Cause

Hàm `_build_transcode_cmd()` (line 77-101) dùng cho post-processing HEVC→H.264:

```python
# line 96-99
elif encoder == "h264_videotoolbox":
    cmd += ["-c:v", encoder, "-b:v", "5M", "-c:a", "copy"]   # ✅ Có bitrate
else:
    cmd += ["-c:v", encoder, "-c:a", "copy"]                  # ❌ Không có gì
```

So sánh:
| Encoder | Quality Params hiện tại | Vấn đề |
|---------|------------------------|--------|
| `libx264` | `-preset ultrafast -crf 23` ✅ | OK |
| `h264_videotoolbox` | `-b:v 5M` ✅ | OK |
| `h264_qsv` (Intel) | ❌ Không có | Dùng FFmpeg default → kết quả không đoán trước |
| `h264_nvenc` (NVIDIA) | ❌ Không có | Tương tự |
| `h264_amf` (AMD) | ❌ Không có | Tương tự |

### Fix

**Before** (line 98-99):
```python
else:
    cmd += ["-c:v", encoder, "-c:a", "copy"]
```

**After**:
```python
else:
    # GPU encoders (h264_qsv, h264_nvenc, h264_amf) — explicit bitrate for consistent quality
    cmd += ["-c:v", encoder, "-b:v", "5M", "-c:a", "copy"]
```

Thêm `-b:v 5M` giống `h264_videotoolbox` — đảm bảo chất lượng nhất quán cho mọi GPU encoder.

---

## Implementation Steps (Thứ tự thực hiện)

1. **Thêm `_build_pip_encode_args(encoder)`** — đặt sau `_build_transcode_cmd()` (sau line 101)
2. **Fix `_build_transcode_cmd()`** — thêm `-b:v 5M` cho QSV/NVENC/AMF ở else branch (line 98-99)
3. **Fix PIP encoder selection** — thay line 242-245 bằng `_detect_hw_encoder()` call
4. **Fix PIP same-URL branch** — update command ở line 248-270: thêm hw_accel + dùng `_build_pip_encode_args()`
5. **Fix PIP dual-input branch** — update command ở line 272-302: thêm hw_accel + dùng `_build_pip_encode_args()`
6. **Test** — quay PIP mode 10-15 giây, playback kiểm tra mượt

---

## Files to Change

| File | Thay đổi |
|------|----------|
| `recorder.py` | Tất cả thay đổi都在文件中 |

## Files to NOT Change

- `api.py` — Không đổi
- `database.py` — Không đổi
- `web-ui/` — Không đổi frontend
- `_detect_hw_encoder()` (line 39-74) — Không sửa, đã hoạt động đúng
- `_is_hevc()` (line 104-125) — Không sửa
- SINGLE mode (line 162-186) — Không sửa, dùng `-c:v copy`
- DUAL_FILE mode (line 188-235) — Không sửa, dùng `-c:v copy`

---

## Cross-Platform Impact

| Platform | PIP Trước Fix | PIP Sau Fix | Post-process Trước | Post-process Sau |
|----------|--------------|-------------|-------------------|-----------------|
| macOS | `h264_videotoolbox` + 2000k | `h264_videotoolbox` + 6M ✅ | 5M ✅ | 5M ✅ (không đổi) |
| Windows (Intel GPU) | `libx264` + 2000k (CPU) ❌ | `h264_qsv` + 6M (GPU) ✅ | Default (không có) ❌ | 5M ✅ |
| Windows (NVIDIA GPU) | `libx264` + 2000k (CPU) ❌ | `h264_nvenc` + 6M (GPU) ✅ | Default (không có) ❌ | 5M ✅ |
| Windows (AMD GPU) | `libx264` + 2000k (CPU) ❌ | `h264_amf` + 6M (GPU) ✅ | Default (không có) ❌ | 5M ✅ |
| Windows (no GPU) | `libx264` + 2000k ❌ | `libx264` + CRF 23 ✅ | CRF 23 ✅ | CRF 23 ✅ (không đổi) |

**Kết luận: Không regression trên bất kỳ platform nào. Chỉ cải thiện.**

---

## Testing

### Test 1: PIP Recording (CAO)
1. Configure station PIP mode
2. Start recording với 1 mã vận đơn
3. Stop sau 10-15 giây
4. Playback file MP4 kết quả
5. **Expected**: Mượt, không giật, PIP overlay rõ

### Test 2: Post-processing HEVC (TRUNG BÌNH)
1. Cần 1 file `.tmp.ts` chứa HEVC (camera main-stream H.265)
2. Trigger stop_recording → chạy `_build_transcode_cmd()`
3. **Expected**: Output MP4 chất lượng tốt, file size hợp lý (~5Mbps)

### Test 3: Non-PIP Modes (Regression check)
1. Quay SINGLE mode → playback mượt
2. Quay DUAL_FILE mode → playback mượt
3. **Expected**: Hoàn toàn giống như trước, không thay đổi

---

## Risk Assessment

- **Risk: THẤP** — Tất cả thay đổi trong 1 file `recorder.py`, không chạm SINGLE/DUAL_FILE modes
- `_detect_hw_encoder()` đã cached → không performance penalty
- Fallback `libx264` + CRF 23 ultrafast luôn hoạt động trên mọi platform
- Bitrate tăng (2M→6M) → file lớn hơn một chút nhưng chất lượng đáng giá
