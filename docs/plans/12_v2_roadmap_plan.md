# V-Pack Monitor v2.0 Roadmap Plan

**Status**: DONE — Implemented in v3.x series.

**Version:** 2.0
**Author:** VDT - Vu Duc Thang (thangvd2)
**Date:** 2026-04-09

---

## Tổng quan

Bản kế hoạch nâng cấp V-Pack Monitor từ v1.4.0 lên v2.0 với 3 phase chính, tập trung vào: độ tin cậy video 100%, phân quyền user + session locking, và multi-camera UI.

---

## Phase 1: Video Pipeline Reliability ✅ COMPLETED (v1.5.0 - 2026-04-09)

**Status:** Đã hoàn thành và push lên GitHub (commit `1a8b375`).

### 1.1 DB Schema: thêm `status` column

Thêm column `status` vào table `packing_video`:

| Status | Màu | Ý nghĩa |
|---|---|---|
| `RECORDING` | 🔴 Đỏ pulse | Đang ghi hình |
| `PROCESSING` | 🟡 Vàng pulse | Đang convert/transcode |
| `READY` | 🟢 Xanh lá | Sẵn sàng xem lại |
| `FAILED` | 🔴 Đỏ static | Lỗi, cần manual xử lý |

**Thay đổi quan trọng:** Record được tạo ở DB **trước** khi FFmpeg start (status=RECORDING), không phải sau khi ghi xong. Đây là điều kiện tiên quyết để crash recovery hoạt động.

```sql
ALTER TABLE packing_video ADD COLUMN status TEXT DEFAULT 'READY';
-- Giữ backward compat: records cũ không có status sẽ mặc định READY
```

### 1.2 VideoWorker: dedicated thread + queue

Tạo `VideoWorker` — 1 background thread chuyên biệt, nhận task qua `queue.Queue`.

```
Barcode SCAN → Tạo DB record (status=RECORDING) → FFmpeg start ghi
Barcode STOP → Đẩy task vào Queue → Trả về ngay → DB: status=PROCESSING
                                   → VideoWorker: stop FFmpeg → convert → verify → DB: status=READY
```

- Queue FIFO, dùng `ThreadPoolExecutor(max_workers=1)` — dễ nâng cấp thành N workers sau nếu cần
- Task types: `stop_and_save`
- Worker log mọi action để debug
- **KHÔNG retry tự động** — nếu convert fail, mark FAILED, admin xử lý
- **Tại sao 1 worker đủ:** Operator không bị block (trạm free ngay khi STOP). H.264 copy chỉ mất 1-3s. HEVC transcode là edge case. GPU encoder chỉ xử lý 1-2 session hiệu quả, chạy parallel không nhanh hơn sequential.

### 1.3 Pre-flight checks (trước khi ghi)

Khi nhận scan request, kiểm tra:
- Disk space ≥ 500MB free
- FFmpeg binary tồn tại
- RTSP URL reachable (quick probe, timeout 3s)
- Station không đang recording

Nếu bất kỳ check nào fail → trả về error rõ ràng, **không bắt đầu ghi**.

### 1.4 Post-processing verify (sau khi ghi)

Sau khi convert MPEG-TS → MP4:
- Verify file exists + size > 0
- Verify FFprobe đọc được metadata (duration > 0, codec valid)
- Nếu convert thất bại → giữ nguyên .ts file, mark FAILED
- **Không retry tự động** — retry tự động có khả năng tạo thêm file corrupt hoặc che giấu lỗi thực sự. Admin manually retry sau khi kiểm tra.

### 1.5 Crash recovery on startup — "Detect & Inform"

**Nguyên tắc: Detect and inform, KHÔNG auto-fix.**

Khi server khởi động:
1. Scan DB cho records có status = RECORDING hoặc PROCESSING
2. Kiểm tra file tương ứng:
   - `.ts` còn + FFprobe valid → convert → mark READY (safe vì FFmpeg đã stop khi crash)
   - `.mp4` đã có + FFprobe valid → mark READY
   - File mất hoàn toàn → mark FAILED
3. **KHÔNG** auto-restart recording
4. **KHÔNG** auto-retry convert nhiều lần
5. Gửi cảnh báo Telegram nếu có bất kỳ record nào FAILED

**Tại sao không auto-retry nhiều lần:**
- Retry che giấu lỗi thực sự (disk full, codec issue, file corrupt)
- Admin cần biết và xử lý gốc vấn đề
- Trong môi trường production, false-positive retry tạo rác và nhầm lẫn

### 1.6 Frontend: Tách biệt 2 loại trạng thái hiển thị

Hệ thống có 2 luồng hoạt động độc lập, cần hiển thị trạng thái riêng biệt:

**Loại 1: Trạng thái quy trình đóng hàng (Live View area)**

Hiển thị trên live view, cho operator biết tiến độ đóng hàng hiện tại:

| State | Hiển thị | Ý nghĩa |
|---|---|---|
| `idle` | Không hiển thị gì / "Sẵn sàng" | Trạm trống, chờ quét mã vạch |
| `packing` | 🔴 "Đang đóng hàng: [MÃ VẠCH]" | Operator đã quét mã, FFmpeg đang ghi |

Khi operator quét STOP → trạng thái quay về `idle` **ngay lập tức**. Operator biết xong việc đóng hàng, không cần chờ video xử lý xong.

Nguồn cập nhật: Barcode scan events (`sendScanAction`) → `packingStatus` state.

**Loại 2: Trạng thái luồng lưu video async (History cards)**

Hiển thị trên từng thẻ trong lịch sử ghi hình, cho biết video xử lý đến đâu:

| State | Hiển thị | Ý nghĩa |
|---|---|---|
| `RECORDING` | 🔴 "Đang ghi hình" | FFmpeg đang quay |
| `PROCESSING` | 🟡 "Đang xử lý" | Đang convert/verify video |
| `READY` | 🟢 "Sẵn sàng" | Xem lại được |
| `FAILED` | ❌ "Lỗi" | Cần admin xử lý |

Nguồn cập nhật: SSE `video_status` event → `record.status` từ DB.

**Tại sao phải tách:**
- Operator quét STOP → đóng hàng xong → live view hiện "Sẵn sàng" (luồng 1 kết thúc)
- Nhưng video vẫn đang convert → history card hiện 🟡 "Đang xử lý" (luồng 2 chưa xong)
- Nếu dùng chung state → operator thấy "Đang xử lý video..." trên live view → nhầm lẫn nghĩ chưa xong việc đóng hàng
- ADMIN cũng cần phân biệt: đóng hàng xong nhưng video chưa ready → biết chờ trước khi xem lại

**Frontend changes (App.jsx):**

- Thay `recordingStatus` state bằng 2 state riêng biệt:
  - `packingStatus`: `"idle"` | `"packing"` — trạng thái đóng hàng, hiển thị trên live view
  - Xóa `recordingStatus` cũ
- `sendScanAction` cập nhật `packingStatus`:
  - Scan mới (start recording) → `setPackingStatus('packing')` + `setCurrentWaybill(barcode)`
  - Scan STOP → `setPackingStatus('idle')` + `setCurrentWaybill('')`
  - Scan same barcode (đang đóng) → không hiện popup, giữ nguyên state
- Live view hiển thị `packingStatus` thay vì `recordingStatus`
- History cards giữ nguyên `record.status` từ DB (RECORDING/PROCESSING/READY/FAILED), hiển thị bằng tiếng Việt
- SSE `video_status` event chỉ cập nhật `record.status` trên history cards, KHÔNG ảnh hưởng `packingStatus`
- Grid view: `stationStatuses` dùng `packingStatus` cho mỗi trạm

**Backend changes (api.py):**

- Không cần thay đổi — API đã trả đúng status cho từng luồng
- `/api/scan` trả `{status: "recording"}` khi bắt đầu ghi → frontend hiểu là `packing`
- `/api/scan` trả `{status: "stopped"}` khi dừng → frontend hiểu là `idle`
- SSE `video_status` push RECORDING→PROCESSING→READY/FAILED → chỉ ảnh hưởng history cards

### 1.7 SSE Event Stream cho realtime updates

**Thay thế polling bằng SSE cho video status + reconnect status.**

Endpoint duy nhất:
```
GET /api/events?stations=1,2,3  →  SSE stream
```

Event types:
- `video_status` — khi RECORDING → PROCESSING → READY/FAILED
- `reconnect_status` — khi tìm thấy IP mới

Frontend subscribe 1 lần, nhận push khi status thay đổi. Không poll.

**Giữ disk health polling 60s** — thay đổi chậm, không đáng đổi sang SSE.

Implementation: FastAPI `StreamingResponse` với `media_type="text/event-stream"`. Không cần thêm thư viện.

**SSE vs Polling — tại sao SSE đáng làm ở đây:**
- Phase 1 thêm status badges → nhiều state transitions cần realtime
- Admin xem grid tất cả trạm → cần thấy status thay đổi ngay
- SSE implementation đơn giản (StreamingResponse + EventSource)
- Giảm từ ~1800 requests/giờ xuống ~60 (keepalive ping only)

**SSE vs Polling — tại sao KHÔNG đáng làm cho disk health:**
- Thay đổi chậm (disk space tăng giảm từ từ)
- Polling 60s overhead negligible
- Thêm SSE cho disk health không mang lại lợi ích nào đáng kể

---

## Phase 2: User Management & Access Control ✅ COMPLETED (v1.6.0 - 2026-04-09)

**Status:** Đã hoàn thành — JWT auth, RBAC (ADMIN/OPERATOR), session locking, user CRUD. PinModal replaced by login form.

### 2.1 Users table + Auth API

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'OPERATOR',  -- ADMIN | OPERATOR
    full_name TEXT NOT NULL,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Auth flow:**
- Login bằng username + password (bcrypt hash)
- Session = JWT token, lưu trong localStorage
- Token expiry: 8h (1 ca làm việc)
- Mỗi request đi kèm token qua header `Authorization: Bearer <jwt>`

### 2.2 RBAC — Role-Based Access Control

| Khả năng | ADMIN | OPERATOR |
|---|---|---|
| Xem live view tất cả trạm | ✅ | ✅ (chỉ trạm được gán) |
| Xem lại video | ✅ | ✅ (chỉ trạm được gán) |
| Quét barcode / đóng hàng | ❌ | ✅ (chỉ 1 trạm lúc active) |
| Cài đặt hệ thống | ✅ | ❌ |
| Xóa video | ✅ | ❌ |
| Quản lý user | ✅ | ❌ |
| Cloud sync | ✅ | ❌ |
| Xem analytics | ✅ | ✅ (chỉ trạm được gán) |

### 2.3 Session Locking — 1 trạm / 1 operator / 1 thời điểm

```sql
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    station_id INTEGER NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_heartbeat TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'ACTIVE',  -- ACTIVE | EXPIRED
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (station_id) REFERENCES stations(id)
);
```

**Luồng hoạt động:**
1. Operator login → chọn trạm → check sessions
2. Nếu trạm free → tạo session ACTIVE
3. Nếu trạm occupied → hiển thị "Trạm đang được sử dụng bởi [username]"
4. Heartbeat mỗi 30s → update last_heartbeat
5. Heartbeat timeout > 90s → auto expire
6. Admin không tạo session — chỉ observe, không đóng hàng

**Edge cases:**
- Operator đóng tab → heartbeat timeout → auto release sau 90s
- Operator mở tab mới cùng trạm → session còn active → cho phép (cùng user)
- Crash server → tất cả sessions ACTIVE → set EXPIRED on startup

### 2.3.1 Station Assignment — Luồng chọn trạm sau khi đăng nhập ⚠️ CHƯA IMPLEMENT

**Vấn đề hiện tại:** Backend API `/api/sessions/acquire`, `/heartbeat`, `/release` đã có sẵn nhưng frontend **không gọi**. Sau khi đăng nhập, user (kể cả OPERATOR) thẳng vào trạm 1 mặc định, không bị bắt chọn trạm, không acquire session, 2 OPERATOR cùng xem/ghi trên 1 trạm mà không có warning.

**Yêu cầu mới (xác nhận bởi VDT 2026-04-10):**

1. **OPERATOR phải chọn trạm sau khi đăng nhập** — không cho vào thẳng trạm mặc định. Hiển thị màn hình chọn trạm (danh sách trạm kèm trạng thái: trống / đang occupied). ADMIN thì bỏ qua bước này, vào thẳng trạm đầu tiên.
2. **OPERATOR chỉ xem/ghi trên trạm đã chọn** — không thể xem trạm khác. Station dropdown bị ẩn hoặc disabled cho OPERATOR. ADMIN xem tất cả trạm tự do.
3. **2 OPERATOR không được dùng cùng trạm** — nếu trạm đã có user khác (session ACTIVE) thì hiện thông báo "Trạm đang được sử dụng bởi [username]" và không cho chọn. ADMIN có thể xem đồng thời với bất kỳ user nào.
4. **OPERATOR đổi trạm** — được phép đổi nếu trạm mới đang trống (không có session ACTIVE của user khác). Khi đổi → release session cũ → acquire session mới.

**Frontend changes (App.jsx):**

- Thêm state `stationAssigned` (boolean) — chỉ `true` khi OPERATOR đã acquire session thành công, hoặc khi user là ADMIN.
- Sau khi login thành công:
  - ADMIN: `setActiveStationId(stations[0].id)` + `setStationAssigned(true)` (như hiện tại).
  - OPERATOR: hiển thị màn hình chọn trạm (danh sách stations + trạng thái occupied/free), gọi `POST /api/sessions/acquire?station_id=X` → nếu success → `setStationAssigned(true)` → vào main UI. Nếu error → hiện message.
- Màn hình chọn trạm: grid/card layout, mỗi trạm hiện tên + trạng thái (🟢 Trống / 🔴 Đang dùng bởi [username]). Trạm occupied bị disable (click không được).
- Khi OPERATOR đổi trạm qua dropdown: gọi `POST /api/sessions/release?station_id=old` → `POST /api/sessions/acquire?station_id=new`. Nếu acquire fail → revert về trạm cũ + hiện error.
- Heartbeat: gọi `POST /api/sessions/heartbeat?session_id=X` mỗi 30s khi `stationAssigned=true` và user là OPERATOR.
- Khi logout: gọi `POST /api/sessions/release?station_id=X`.
- ADMIN không gọi acquire/heartbeat/release — admin skip station locking hoàn toàn.

**Backend changes (api.py):**

- `POST /api/sessions/acquire` — đã có, hoạt động đúng. Thêm audit log.
- `POST /api/sessions/heartbeat` — đã có, hoạt động đúng.
- `POST /api/sessions/release` — đã có, hoạt động đúng.
- Thêm `GET /api/sessions/station-status` — trả về danh sách tất cả trạm + trạng thái occupied/free + username nếu occupied. Dùng cho màn hình chọn trạm của OPERATOR.
- Tất cả API ghi hình (`POST /api/scan`, `POST /api/stop`) thêm check: OPERATOR chỉ ghi trên trạm có session ACTIVE của mình. ADMIN không ghi (như hiện tại).

### 2.4 Frontend: Login page, user menu, role-aware UI

- Login page (username + password)
- Header hiển thị tên user + role
- Ẩn/hiện chức năng theo role
- Logout button

---

## Phase 3: Multi-Camera Live View UI ✅ COMPLETED (v1.7.0 - 2026-04-09)

**Status:** Đã hoàn thành — Overview Grid, click-to-zoom, per-station status, responsive grid.

**Mục tiêu:** Hiển thị live view cho tất cả camera, hỗ trợ nhiều mode.

### 3.1 Overview Grid layout

- Toggle giữa "Single Station View" và "Overview Grid" bằng button ở header
- Grid tự động tính số cột dựa trên số trạm (2x2, 3x2, v.v.)

```
┌─────────────────┬─────────────────┐
│  Bàn Chốt Đơn 1 │  Bàn Gói Hàng 2 │
│    [LIVE]        │    [LIVE]        │
│   🔴 Recording   │   🟢 Idle        │
└─────────────────┴─────────────────┘
```

### 3.2 Mode-aware display

- **Single mode:** 1 camera lớn
- **Dual mode:** 2 iframe cạnh nhau (cam1 + cam2)
- **PIP mode:** 1 iframe lớn + 1 small overlay

### 3.3 Click-to-zoom interaction

- Click vào ô grid → zoom thành single view
- Nút "Back to Grid" để quay lại overview

### 3.4 Responsive grid

- Mobile: stack dọc (1 column)
- Tablet: 2 columns
- Desktop: auto-fill dựa trên số trạm

---

## Priority Order

```
Phase 1 → Phase 2 → Phase 3
```

- **Phase 1** là nền tảng — phải làm trước để đảm bảo 100% video
- **Phase 2** quan trọng cho production multi-user
- **Phase 3** là UX improvement

---

## Technical Decisions

### SSE cho realtime status

Sử dụng **SSE (Server-Sent Events)** cho video status + reconnect status:
- 1 endpoint multiplex duy nhất: `GET /api/events?stations=1,2,3`
- Server push event khi status thay đổi
- Frontend subscribe 1 lần, không cần poll
- Implementation: FastAPI `StreamingResponse`, không cần thêm thư viện
- Giữ disk health polling 60s (không đáng đổi sang SSE)

### Crash Recovery — Detect & Inform

Chiến lược "Detect & Inform", KHÔNG auto-fix:
- Startup scan DB records có status = RECORDING/PROCESSING
- Verify file existence, attempt 1 lần convert nếu .ts còn
- Mark FAILED nếu không recover được + cảnh báo Telegram
- **KHÔNG** auto-restart recording
- **KHÔNG** auto-retry nhiều lần

### Telegram Alert Rules

| Trường hợp | Cảnh báo? | Lý do |
|---|---|---|
| File mất → FAILED | ✅ Gửi Telegram ngay | Sự cố nghiêm trọng, cần xử lý |
| Server crash, recording dừng | ❌ Không gửi | Operator tự quét lại, không cần can thiệp admin |
| .ts còn → convert thành công → READY | ❌ Không gửi | Recovery thành công, không có vấn đề |
| .ts còn → convert thất bại → FAILED | ✅ Gửi Telegram | Video có nhưng không convert được, admin cần xử lý |

### VideoWorker — Single Worker FIFO

Sử dụng `ThreadPoolExecutor(max_workers=1)` cho video processing queue:
- 1 worker đủ cho workload 2-5 trạm kho
- Operator không bị block (trạm free ngay khi STOP)
- H.264 copy (90%+ trường hợp) chỉ mất 1-3s
- HEVC transcode là edge case, GPU chỉ xử lý 1-2 session hiệu quả
- Thiết kế để dễ nâng cấp: chỉ cần đổi `max_workers=N` nếu cần sau này

### Smart Storage — Tạm hoãn

Không implement trong v2.0. Sẽ xem xét lại khi có nhu cầu thực tế.
