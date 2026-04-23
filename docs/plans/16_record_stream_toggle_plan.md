# Kế Hoạch #16: Record Stream Toggle (Main/Sub Stream Switcher)

**Status**: DONE — Implemented in v3.x series.

**Phiên bản:** v2.2.3
**Ngày lập:** 2026-04-12
**Ngày hoàn thành:** 2026-04-12
**Mức ưu tiên:** HIGH
**Trạng thái:** COMPLETED (partial — toggle UI + backend done, MediaMTX re-stream reverted)

---

## Tổng Quan

Camera Tenda CH10 bị quá tải khi FFmpeg kéo main-stream đồng thời với MediaMTX kéo sub-stream cho live view. Cần thêm toggle cho phép user chọn record từ **main-stream** (chất lượng cao) hoặc **sub-stream** (ổn định hơn, ít tải camera).

## Vấn Đề

| Stream | Connections khi record | CH10 chịu nổi? |
|--------|----------------------|----------------|
| Main (2880x1620 / 1920x1080) | 2-4 (live sub + record main × số lens) | Không — vỡ hình, mất frame |
| Sub (768x432) | 1-2 (MediaMTX + FFmpeg cùng sub) | Có — ổn định |

Camera Imou không bị vì chỉ SINGLE mode (2 connections). CH10 PIP dual-lens cần 4 connections → quá tải.

## Thiết Kế

### 1. Backend — System Setting

Thêm setting `RECORD_STREAM_TYPE` vào `system_settings` table:
- Giá trị: `"main"` hoặc `"sub"` (mặc định: `"main"`)
- Đọc trong recording flow để quyết định dùng `get_rtsp_url()` hay `get_rtsp_sub_url()`

**File: `api.py`**

Sửa hàm recording (khoảng line 1033):
```python
# Trước
url1 = get_rtsp_url(ip1, code, channel=1, brand=brand)

# Sau
record_stream = database.get_setting("RECORD_STREAM_TYPE", "main")
if record_stream == "sub":
    url1 = get_rtsp_sub_url(ip1, code, channel=1, brand=brand)
else:
    url1 = get_rtsp_url(ip1, code, channel=1, brand=brand)
```

Tương tự cho url2 (camera 2 / channel 2).

**File: `api.py` — Settings API**

Thêm `RECORD_STREAM_TYPE` vào `SettingsUpdate` model:
```python
class SettingsUpdate(BaseModel):
    RECORD_KEEP_DAYS: int
    RECORD_STREAM_TYPE: str = "main"  # "main" or "sub"
    CLOUD_PROVIDER: str = "NONE"
    ...
```

### 2. Frontend — Toggle Button

Thêm nút toggle trong header, cạnh camera mode selector:
- **Vị trí:** Ngang hàng với toggle Dual/PIP, chỉ hiện khi đang xem single view
- **UI:** 2 nút nhỏ: `1080p` (main) / `480p` (sub) — hoặc icon-based
- **Label:** "Rec: Main" / "Rec: Sub" để rõ nghĩa
- **Chỉ ADMIN mới thấy** (operator không cần quan tâm)

**File: `web-ui/src/App.jsx`**

- Thêm state `recordStreamType` từ settings
- Toggle gọi `POST /api/settings` để lưu backend
- Nút nằm cạnh camera mode toggle (1 Cam / Dual / PIP)

**Hoặc đơn giản hơn:** Thêm vào **SetupModal** trong phần settings. Nhưng user yêu cầu "nút trên UI" để switch nhanh → toggle button trên header.

### 3. Chi Tiết UI

```
[Trạm: Station 1 ▼] [+]
[Rec: 1080p | 480p]    ← Nút toggle mới (ADMIN only, single view only)
[1 Cam | Dual | PIP]
```

- Active button: `bg-blue-500/20 text-blue-300`
- Inactive button: `text-slate-400 hover:text-white`
- Khi bấm → gọi API lưu setting → hiển thị toast "Đổi record stream thành công"
- Chỉ có hiệu lực cho **lần ghi tiếp theo** (không ảnh hướng recording đang chạy)

## Files Cần Sửa

| File | Thay đổi |
|------|----------|
| `api.py` | `SettingsUpdate` thêm `RECORD_STREAM_TYPE`, recording flow đọc setting |
| `web-ui/src/App.jsx` | Toggle button, state, API call |

## Testing

- [x] Toggle sang "Sub" → ghi video → verify video sub-stream
- [x] Toggle sang "Main" → ghi video → verify video main-stream
- [x] Toggle không ảnh hưởng live view
- [x] Toggle không ảnh hưởng recording đang chạy
- [x] Operator không thấy toggle

## Đã Hoàn Thành

1. **Backend:** `RECORD_STREAM_TYPE` setting + recording flow đọc setting để chọn main/sub
2. **Frontend:** Nút toggle "Rec: 1080p / 480p" (ADMIN only)
3. **Bug fix:** `delete_station` race condition (`del` → `pop`)

## Đã Revert

- **MediaMTX main-stream + re-stream recording:** Đã thử đổi MediaMTX sang main-stream + FFmpeg record từ `localhost:8554` → gây `OSError: Invalid argument` khi stop recording. Đã revert hoàn toàn.
- **Nguyên nhân:** Camera Tenda CH10 bị quá tải, đã quyết định trả lại camera Tenda, sẽ mua Imou cao cấp hơn.
- **Revert recorder.py:** `stdin.close()` → quay lại `stdin.write(b"q\n")`

## Ghi Chú

- Giải pháp MediaMTX re-stream (`rtsp://localhost:8554/station_1`) → chỉ 1 connection đến camera. Sẽ thử lại khi có camera tốt hơn.
- Sub-stream 768x432 @ 1024kbps đủ cho monitoring đóng hàng, đọc mã vạch OK.
- Setting lưu DB → restart server vẫn giữ.
- Toggle "Rec: 1080p/480p" vẫn giữ trong code — hữu ích cho camera đời sau.
