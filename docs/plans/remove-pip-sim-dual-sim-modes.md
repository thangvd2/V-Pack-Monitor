# Plan: Xóa hoàn toàn camera modes PIP SIM và DUAL SIM

**Ngày**: 2026-04-22
**Mức độ**: Medium — Remove unused camera modes
**Loại**: Feature removal / Cleanup

---

## Background

`pip_sim` và `dual_file_sim` là 2 chế độ "giả lập" — dùng 1 camera để tạo 2 luồng bằng FFmpeg `split`. Trong thực tế:
- Camera 1 mắt → chỉ nên dùng `SINGLE` mode
- Camera 2 mắt (dual-lens như Dahua Hero Dual D1) → dùng `pip` hoặc `dual_file` mode với `ip_camera_2` để trống

`_sim` modes gây nhầm lẫn, tạo EOF error trên MediaMTX, và không có use case thực tế rõ ràng.

---

## Key Insight: Xóa _sim KHÔNG gây mất tính năng

Recorder đã tự handle case "1 camera dùng PIP" thông qua so sánh URL:

**`recorder.py:247`**:
```python
if self.rtsp_url_1 == self.rtsp_url_2:  # Same stream → FFmpeg split
    command = [... "-filter_complex", "[0:v]split=2[main][pip_raw]..." ...]
else:  # Different streams → 2 inputs
    command = [... "-i", self.rtsp_url_1, "-i", self.rtsp_url_2, ...]
```

**`recorder.py:131`**:
```python
self.rtsp_url_2 = rtsp_url_2 if rtsp_url_2 else rtsp_url_1  # Fallback to url1
```

→ Nếu camera 1 mắt chọn mode `pip` hoặc `dual_file` mà `ip_camera_2` trống:
- `url2 = url1` (fallback trong recorder)
- FFmpeg sẽ dùng `split` filter → hoạt động y hệt `pip_sim`/`dual_file_sim`

**Kết luận**: Xóa `_sim` modes **không mất tính năng nào**. Người dùng chỉ cần chọn `pip` hoặc `dual_file` thay vì `pip_sim` hoặc `dual_file_sim`.

---

## Files cần sửa

### 1. `web-ui/src/SetupModal.jsx` — Xóa dropdown options và descriptions

**Line 65-71** — Xóa `pip_sim` và `dual_file_sim` khỏi `CAMERA_MODE_DESC`:
```javascript
// SỬA TỪ:
const CAMERA_MODE_DESC = {
  single: 'Ghi 1 luồng từ 1 camera',
  pip: 'Ghép hình-in-picture từ 2 camera (hoặc 1 camera 2 mắt)',
  pip_sim: 'Ghép PIP thử nghiệm từ 1 camera',
  dual_file: 'Ghi 2 file riêng từ 2 camera (hoặc 1 camera 2 mắt)',
  dual_file_sim: 'Ghi 2 file riêng từ 1 camera',
};

// SỬA THÀNH:
const CAMERA_MODE_DESC = {
  single: 'Ghi 1 luồng từ 1 camera',
  pip: 'Ghép hình-in-picture từ 2 camera (hoặc 1 camera 2 mắt)',
  dual_file: 'Ghi 2 file riêng từ 2 camera (hoặc 1 camera 2 mắt)',
};
```

**Line 625-629** — Xóa 2 `<option>` tags:
```html
<!-- XÓA 2 dòng này: -->
<option value="pip_sim">PIP SIM — Ghép thử từ 1 camera</option>
<option value="dual_file_sim">DUAL SIM — 2 file từ 1 camera</option>
```

### 2. `routes_records.py` — Simplify mode → record_mode mapping

**Line 160-173** — Gộp `_sim` cases vào parent mode:

```python
# SỬA TỪ:
url1 = api.get_rtsp_url(ip1, code, channel=1, brand=brand)
if c_mode in ["dual_file", "pip"]:
    url2 = api.get_rtsp_url(ip2 if ip2 else ip1, code, channel=2, brand=brand)
elif c_mode in ["dual_file_sim", "pip_sim"]:
    url2 = url1
else:
    url2 = url1

if c_mode in ["dual_file", "dual_file_sim"]:
    r_mode = "DUAL_FILE"
elif c_mode in ["pip", "pip_sim"]:
    r_mode = "PIP"
else:
    r_mode = "SINGLE"

# SỬA THÀNH:
url1 = api.get_rtsp_url(ip1, code, channel=1, brand=brand)
if c_mode == "dual_file":
    url2 = api.get_rtsp_url(ip2 if ip2 else ip1, code, channel=2, brand=brand)
elif c_mode == "pip":
    url2 = api.get_rtsp_url(ip2 if ip2 else ip1, code, channel=2, brand=brand)
else:
    url2 = url1

if c_mode == "dual_file":
    r_mode = "DUAL_FILE"
elif c_mode == "pip":
    r_mode = "PIP"
else:
    r_mode = "SINGLE"
```

**Lưu ý**: Sau khi xóa `_sim`, nếu DB có stations cũ với `camera_mode = "pip_sim"` hoặc `"dual_file_sim"`, `c_mode` sẽ không match bất kỳ `if/elif` nào → rơi vào `else` → `url2 = url1` và `r_mode = "SINGLE"`. Đây là **graceful fallback** — không crash, chỉ ghi 1 luồng.

### 3. `docs/USER_GUIDE_ADMIN.md` — Xóa 2 rows trong camera mode table

- Line 146: Xóa row `| **PIP SIMULATION** | Giống PIP nhưng dùng chế độ mô phỏng |` (xóa cả blank line sau nếu có)
- Line 148: Xóa row `| **DUAL SIMULATION** | Giống DUAL_FILE nhưng dùng chế độ mô phỏng |`

### 4. `docs/plans/19_setup_modal_upgrade_plan.md` — Xóa references

- Line 60: Xóa dòng mention `pip_sim` hoặc `dual_file_sim`
- Lines 92-94: Xóa 2 dòng descriptions

### 5. `web-dist/` — Rebuild sau khi xóa

- File `web-dist/assets/index-DxzW5QAo.js` vẫn chứa `pip_sim`/`dual_file_sim` (built artifact)
- **Không sửa trực tiếp** — chạy `npm run build` trong `web-ui/` sẽ regenerate

---

## Files KHÔNG cần sửa

| File | Lý do |
|---|---|
| `recorder.py` | Không reference `_sim` — chỉ dùng `SINGLE`, `DUAL_FILE`, `PIP` (record_mode, không phải camera_mode) |
| `api.py` | Không reference `_sim` — chỉ check `PIP` và `DUAL_FILE` |
| `routes_stations.py` | `_resolve_cam2_url` chỉ check `pip`, `dual_file` — đã clean từ Round 2 |
| `App.jsx` | `isDualCamStation` chỉ check `pip`, `dual_file` — đã clean từ Round 2 |
| `database.py` | Schema không enforce mode values — chỉ lưu string |
| `tests/` | Không có test nào reference `pip_sim` hoặc `dual_file_sim` |

---

## Migration / Backward Compatibility

**Stations cũ có `camera_mode = "pip_sim"` hoặc `"dual_file_sim"` trong DB:**
- `routes_records.py` sẽ fallback về `SINGLE` mode (ghi 1 luồng) — không crash
- **Không cần DB migration** — user có thể tự cập nhật station setting qua UI
- **Gợi ý (optional)**: Thêm logic auto-migrate trong `api.py` lifespan init:
  ```python
  # Auto-migrate deprecated modes
  mode = st.get("camera_mode", "SINGLE").upper()
  if mode in ("PIP_SIM", "DUAL_FILE_SIM"):
      migrated = "PIP" if mode == "PIP_SIM" else "DUAL_FILE"
      logger.info(f"Auto-migrating station {st['id']} from {mode} to {migrated}")
      # Update DB
  ```
  Đây là optional — bro quyết định có cần không.

---

## Test Cases

1. **Chọn mode SINGLE** → dropdown chỉ có 3 options (SINGLE, PIP, DUAL FILE) → record 1 luồng
2. **Chọn mode PIP với ip_camera_2 trống** → url2 = url1 → FFmpeg split → ghi PIP đúng
3. **Chọn mode PIP với ip_camera_2 khác** → url2 từ ip_camera_2 → FFmpeg 2 inputs → ghi PIP đúng
4. **Chọn mode DUAL FILE với ip_camera_2 trống** → url2 = url1 → 2 files cùng content → ghi đúng
5. **Station cũ camera_mode="pip_sim" trong DB** → graceful fallback SINGLE, không crash
6. **`pytest tests/ -v`** pass
7. **`npm run build && npm run lint`** pass
8. **`web-dist/` regenerated** — không còn pip_sim/dual_file_sim trong built JS

---

## Summary

| # | File | Action |
|---|------|--------|
| 1 | `web-ui/src/SetupModal.jsx` | Xóa 2 entries trong CAMERA_MODE_DESC + 2 option tags |
| 2 | `routes_records.py` | Simplify if/elif — bỏ `_sim` branches |
| 3 | `docs/USER_GUIDE_ADMIN.md` | Xóa 2 rows PIP SIMULATION / DUAL SIMULATION |
| 4 | `docs/plans/19_setup_modal_upgrade_plan.md` | Xóa references |
| 5 | `web-dist/` | Rebuild via `npm run build` |
