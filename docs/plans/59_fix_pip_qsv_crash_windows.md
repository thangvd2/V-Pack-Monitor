# Plan 59: Fix PIP Recording Crash with QSV GPU Encoder on Windows

**Ngày**: 2026-04-25
**Mức độ**: HIGH — Tất cả PIP recordings fail trên Windows + Intel GPU
**Loại**: Bug fix (backend)

---

**Status**: Done — PR #67 merged to dev

## Problem

PIP mode recording crash trên Windows với Intel GPU (h264_qsv). FFmpeg exit ngay lập tức, không tạo video file.

**FFmpeg error:**
```
Filter 'setpts:default' has output 0 (out) unconnected
Error binding filtergraph inputs/outputs: Invalid argument
Incompatible pixel format 'yuv420p' for codec 'h264_qsv', auto-selecting format 'nv12'
```

**Root cause:** PR #45 + #46 refactor PIP recording trên macOS (h264_videotoolbox). Trên macOS `hw_accel=""` nên không thêm `-hwaccel` flag. Nhưng trên Windows, `_detect_hw_encoder()` trả về `("h264_qsv", "-hwaccel qsv")`, dẫn đến 3 lỗi.

---

## 3 Bugs chi tiết

### Bug 1: `[out]` label không được map (recorder.py:284)

**Same-camera PIP branch:**
```python
"[0:v]split=2[main][pip_raw]; [pip_raw]scale=iw/3:-1[pip]; [main][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10, setpts=PTS-STARTPTS[out]"
```

Filter output `[out]` không có `-map "[out]"` → FFmpeg crash.

**Different-camera branch** (line 316) KHÔNG có `[out]` → auto-map OK.

**Fix:** Remove `[out]` label, giống different-camera branch:
```python
"...overlay=main_w-overlay_w-10:main_h-overlay_h-10, setpts=PTS-STARTPTS"
```

### Bug 2: `-hwaccel qsv` xung đột với software filter_complex (recorder.py:274-275)

```python
if hw_accel:
    command += hw_accel.split()  # adds "-hwaccel qsv"
```

`-hwaccel qsv` → hardware decode → GPU frames → filter_complex (split/scale/overlay = software) → format mismatch → FFmpeg crash.

**Fix:** KHÔNG thêm `hw_accel` cho PIP mode. Software decode + filter, GPU chỉ encode:
```python
# PIP mode: skip hw_accel (filter_complex needs software frames)
# GPU encoder still used for encoding via _build_pip_encode_args()
```

### Bug 3: `-pix_fmt yuv420p` incompatible với h264_qsv (recorder.py:127)

```python
# _build_pip_encode_args for GPU encoders:
"-pix_fmt", "yuv420p",  # ← QSV needs nv12, not yuv420p
```

**Fix:** Remove `-pix_fmt yuv420p` cho GPU encoders, let FFmpeg auto-select:
```python
else:
    # GPU encoders (h264_qsv, h264_nvenc, h264_amf)
    return [
        "-c:v", encoder,
        "-b:v", "6M",
        # No -pix_fmt — let FFmpeg auto-select (nv12 for QSV)
    ]
```

---

## Scope

### Files to change:

| File | Thay đổi |
|------|----------|
| `recorder.py:284` | Remove `[out]` label từ same-camera PIP filter_complex |
| `recorder.py:274-275` | Skip `hw_accel` cho PIP mode (both branches) |
| `recorder.py:127` | Remove `-pix_fmt yuv420p` từ GPU encoder args |
| `recorder.py:300-301` | Skip `hw_accel` cho different-camera PIP branch |

### Changes chi tiết:

#### 1. Fix same-camera PIP filter_complex (line 284)

```python
# BEFORE:
"[0:v]split=2[main][pip_raw]; [pip_raw]scale=iw/3:-1[pip]; [main][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10, setpts=PTS-STARTPTS[out]",

# AFTER:
"[0:v]split=2[main][pip_raw]; [pip_raw]scale=iw/3:-1[pip]; [main][pip]overlay=main_w-overlay_w-10:main_h-overlay_h-10, setpts=PTS-STARTPTS",
```

#### 2. Skip hw_accel cho PIP mode (both branches)

```python
# BEFORE (line 273-275):
command = ["ffmpeg", "-y", "-fflags", "+genpts+discardcorrupt"]
if hw_accel:
    command += hw_accel.split()

# AFTER:
command = ["ffmpeg", "-y", "-fflags", "+genpts+discardcorrupt"]
# NOTE: PIP filter_complex uses software filters (split, scale, overlay)
# -hwaccel qsv/nvenc would create GPU frames incompatible with software filters
# GPU encoder is still used for encoding via _build_pip_encode_args()
```

Same cho different-camera branch (line 299-301).

#### 3. Fix GPU encoder pix_fmt (line 122-128)

```python
# BEFORE:
else:
    return [
        "-c:v", encoder,
        "-b:v", "6M",
        "-pix_fmt", "yuv420p",  # ← incompatible with h264_qsv
    ]

# AFTER:
else:
    return [
        "-c:v", encoder,
        "-b:v", "6M",
        # No -pix_fmt — QSV auto-selects nv12, NVENC/AMF handle yuv420p natively
    ]
```

#### 4. Close stdin pipe explicitly (line 362-387)

Thêm `p.stdin.close()` sau khi process exit — fix `OSError: [Errno 22]` warning:

```python
for pinfo in self.processes:
    p = pinfo["proc"]
    try:
        p.wait(timeout=30)
    except subprocess.TimeoutExpired:
        ...
    finally:
        try:
            p.stdin.close()
        except Exception:
            pass
```

---

## Constraints

- SINGLE mode dùng `-c copy` (no encode) → không affected
- DUAL_FILE mode dùng `-c copy` (no encode) → không affected
- Chỉ PIP mode bị ảnh hưởng (filter_complex + re-encode)
- Test trên cả Windows (QSV) và macOS (VideoToolbox) nếu possible
- VideoToolbox không có `hw_accel` extra args → skip logic không ảnh hưởng macOS

---

## Verification

- [ ] PIP recording trên Windows + Intel GPU → FFmpeg không crash
- [ ] `.tmp.ts` file được tạo → remux thành `.mp4` thành công
- [ ] `pytest tests/ -v` pass (test_recorder.py)
- [ ] SINGLE mode vẫn hoạt động (regression check)
- [ ] DUAL_FILE mode vẫn hoạt động (regression check)
- [ ] Không có `OSError [Errno 22]` warning trong logs
- [ ] Video PIP play được, PIP overlay đúng vị trí
