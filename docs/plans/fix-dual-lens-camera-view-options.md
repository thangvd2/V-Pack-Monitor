# Bug Fix: Dual-lens camera (1 IP, 2 mắt) không hiển thị view options

**Ngày phát hiện**: 2026-04-22
**Ngày review**: 2026-04-22
**Mức độ**: Medium — Camera Dahua Hero Dual D1 (2 mắt, 1 IP) không dùng được Dual/PIP view
**Loại**: Logic bug (cả frontend + backend)
**Trạng thái**: Round 1 đã implement bởi Antigravity → Cần fix 2 issues từ review

---

## Root Cause

Camera Dahua Hero Dual D1 có **1 IP nhưng 2 channel** (Fixed lens = channel 1, PTZ = channel 2). Khi `ip_camera_2` để trống (đúng vì chỉ cần 1 IP), hệ thống không nhận ra đây là dual-cam:

**Frontend** (`App.jsx:926`):
```js
const hasCam2 = activeStation?.ip_camera_2 && activeStation.ip_camera_2.trim() !== '';
```
→ Luôn `false` khi `ip_camera_2` trống → view options (1 Cam/Dual/PIP) bị ẩn.

**Backend** (`routes_stations.py:77-84`, `api.py:544-550`):
```python
cam2_url = None
if payload.ip_camera_2:  # ← Empty string → cam2_url = None
```
→ Không tạo stream `station_{id}_cam2` cho channel 2 → Dù frontend hiện view options thì Dual/PIP cũng không có nguồn stream.

---

## Round 1 — Đã implement ✅

### 1. Backend: Helper `_resolve_cam2_url` trong `routes_stations.py` ✅

### 2. Backend: `api.py` lifespan init fallback ✅

### 3. Frontend: `isDualCamStation()` helper trong `App.jsx` ✅

### 4. Frontend: Grid badge "2 CAM" dùng helper ✅

### 5. Tests pass ✅ — 322/322 pytest, npm run build + lint pass

---

## Round 2 — Cần fix (từ OpenCode review)

### Fix 1: Bỏ `pip_sim` và `dual_file_sim` khỏi dual-mode check

**Vấn đề**: Antigravity thêm `pip_sim` và `dual_file_sim` vào danh sách modes sinh cam2_url, nhưng:
- `pip_sim` = "ghép PIP thử từ 1 camera" — designed cho camera **1 mắt**
- Camera 1 mắt không có channel 2 → MediaMTX cố connect `channel=2` → EOF error (như lỗi `station_1_cam2` đang gặp)
- Recording path (`routes_records.py:163-164`) vẫn dùng `url2 = url1` cho `_sim` modes → không cần cam2 stream
- Nếu camera 2 mắt dùng `pip_sim` mode, live view sẽ hiện channel 2 nhưng recording chỉ ghi channel 1 duplicated → inconsistency

**Chỉ giữ `pip` và `dual_file`** — đúng plan gốc, đúng ngữ nghĩa.

**File: `routes_stations.py`** — `_resolve_cam2_url` (hiện tại line ~30):

```python
# SỬA TỪ:
if payload.camera_mode.lower() in ('pip', 'dual_file', 'pip_sim', 'dual_file_sim'):

# SỬA THÀNH:
if payload.camera_mode.lower() in ('pip', 'dual_file'):
```

**File: `api.py`** — Lifespan init (hiện tại line ~552):

```python
# SỬA TỪ:
elif mode in ("PIP", "DUAL_FILE", "PIP_SIM", "DUAL_FILE_SIM"):

# SỬA THÀNH:
elif mode in ("PIP", "DUAL_FILE"):
```

**File: `App.jsx`** — `isDualCamStation` helper (hiện tại line ~928):

```javascript
// SỬA TỪ:
const isDualMode = ['pip', 'pip_sim', 'dual_file', 'dual_file_sim'].includes(station.camera_mode?.toLowerCase());

// SỬA THÀNH:
const isDualMode = ['pip', 'dual_file'].includes(station.camera_mode?.toLowerCase());
```

### Fix 2: Revert formatting rác trong eslint.config.js và vite.config.js

**Vấn đề**: Prettier format lại 2 file này (thêm semicolons, collapse arrays) — không liên quan đến bug fix. Làm diff nhiễu.

**Yêu cầu**: Revert `web-ui/eslint.config.js` và `web-ui/vite.config.js` về state ban đầu:

```bash
git checkout web-ui/eslint.config.js web-ui/vite.config.js
```

---

## Files cần sửa Round 2

| File | Vị trí | Thay đổi |
|---|---|---|
| `routes_stations.py` | `_resolve_cam2_url()` helper | Bỏ `pip_sim`, `dual_file_sim` khỏi mode check |
| `api.py` | Lifespan init cam2_url fallback | Bỏ `PIP_SIM`, `DUAL_FILE_SIM` khỏi mode check |
| `App.jsx` | `isDualCamStation()` helper | Bỏ `pip_sim`, `dual_file_sim` khỏi DUAL_MODES |
| `web-ui/eslint.config.js` | Toàn bộ | `git checkout` revert về gốc |
| `web-ui/vite.config.js` | Toàn bộ | `git checkout` revert về gốc |

---

## Test Cases (cập nhật)

1. **Camera 2 mắt, ip_camera_2 để trống, mode=PIP** → cam2_url được sinh từ ip_camera_1 channel=2, view options hiện đúng ✅
2. **Camera 1 mắt, ip_camera_2 trống, mode=SINGLE** → hasCam2=false, không hiện view options (không regression) ✅
3. **Camera 2 mắt, ip_camera_2 điền IP khác, mode=PIP** → cam2_url dùng ip_camera_2 (existing behavior không đổi) ✅
4. **Camera 1 mắt, mode=PIP_SIM** → hasCam2=false, KHÔNG sinh cam2_url → không có MediaMTX EOF error ✅ **(NEW)**
5. **Restart hệ thống** → Lifespan init đúng cam2_url cho dual-lens camera ✅
6. **`pytest tests/ -v`** pass ✅
7. **`npm run build && npm run lint`** trong `web-ui/` pass ✅
8. **`git diff` chỉ chứa 3 file: routes_stations.py, api.py, App.jsx** — không có formatting rác ✅ **(NEW)**

---

## KHÔNG sửa

- `SetupModal.jsx` — label "Để trống nếu dùng 1 camera có 2 mắt" đã đúng
- `database.py` — Không đụng, schema OK
- `MODES_NEED_IP2` trong SetupModal — Vẫn show IP2 field cho pip/dual_file (user có thể điền hoặc để trống)
- `routes_records.py` — Đã đúng, không cần sửa
- `routes_system.py` — Đã có fallback `ip_camera_2 or ip`, không cần sửa
