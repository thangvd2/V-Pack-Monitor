# V-Pack Monitor v3.0 Roadmap Plan

**Version:** 3.0
**Author:** VDT - Vu Duc Thang (thangvd2)
**Date:** 2026-04-09

---

## Tổng quan

Bản kế hoạch nâng cấp V-Pack Monitor từ v1.7.0 lên v3.0 với 4 phase, tập trung vào: quản trị user chuyên nghiệp, analytics nâng cao, multi-camera nâng cấp, và monitoring hệ thống.

**Yêu cầu tạm hoãn:** Smart Storage (tự động dọn video cũ, tiered storage).

---

## Phase 1: User Management UI + Security ✅ COMPLETED (v1.8.0 - 2026-04-09)

**Status:** Đã hoàn thành — UserManagementModal, change password, audit log, session management.

**Mục tiêu:** Hoàn thiện trải nghiệm quản trị user — hiện API đã có đầy đủ nhưng frontend thiếu hoàn toàn.

### 1.1 User Management Modal (ADMIN only)

**UI Component:** `UserManagementModal.jsx` (mới)

- Nút "Quản lý người dùng" ở header (chỉ ADMIN thấy, icon `Users` đã import)
- Mở modal danh sách user dạng bảng:
  | Username | Họ tên | Vai trò | Trạng thái | Thao tác |
  |---|---|---|---|---|
  | admin | VDT | ADMIN | 🟢 Active | Đổi mật khẩu |
  | operator1 | Nguyễn Văn A | OPERATOR | 🟢 Active | Sửa / Khoá / Xoá |
- Nút "Thêm người dùng" → form inline/modal con
- Sửa user: đổi full_name, role, is_active
- Khoá/Mở tài khoản: toggle `is_active` (không xoá, giữ data)
- Xoá user: confirm dialog, không xoá chính mình
- Đổi mật khẩu: input mới → gọi `PUT /api/users/{id}/password`

**API đã có sẵn (không cần sửa backend):**
- `GET /api/users` → list users
- `POST /api/users` → create user
- `PUT /api/users/{id}` → update user
- `PUT /api/users/{id}/password` → reset password
- `DELETE /api/users/{id}` → delete user

### 1.2 Đổi mật khẩu cho chính mình

- Menu dropdown khi click vào tên user ở header
- Options: "Đổi mật khẩu", "Đăng xuất"
- Form đổi pass: mật khẩu cũ + mật khẩu mới + xác nhận
- Cần thêm 1 endpoint: `PUT /api/auth/change-password` (body: `{old_password, new_password}`)

### 1.3 Session Management View

- Hiển thị trong User Management Modal, tab "Phiên hoạt động"
- Bảng sessions đang ACTIVE: User / Trạm / Bắt đầu / Heartbeat cuối
- ADMIN có thể force-end session (kick user)
- API đã có: `GET /api/users`, cần thêm `GET /api/sessions/active` và `DELETE /api/sessions/{id}`

### 1.4 Audit Log cơ bản

- Thêm bảng `audit_log` trong SQLite:
  ```sql
  CREATE TABLE audit_log (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER,
      action TEXT NOT NULL,        -- LOGIN, LOGOUT, CREATE_USER, DELETE_USER, START_RECORD, STOP_RECORD, CHANGE_PASSWORD, etc.
      details TEXT,                -- JSON string với context
      station_id INTEGER,
      created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (user_id) REFERENCES users(id)
  );
  ```
- Ghi log tự động trong api.py cho các action quan trọng
- Tab "Nhật ký" trong User Management Modal (ADMIN only)
- Filter theo user, action type, date range

---

## Phase 2: Dashboard & Analytics Pro

**Mục tiêu:** Biểu đồ và thống kê chuyên nghiệp cho quản lý kho.

### 2.1 Overview Dashboard Page

**UI:** Toggle giữa current view và Dashboard view (button ở header)

Dashboard widgets:
- **Tổng đơn hôm nay** (toàn kho + từng trạm) — số lớn + trend so với hôm qua
- **Biểu đồ sản xuất theo giờ** — bar chart, trục X = giờ (8h-22h), trục Y = số đơn
- **Top trạm năng suất** — ranking stations by today's output
- **Video storage** — dung lượng đã dùng + trend 7 ngày
- **System uptime** — thời gian server đã chạy

### 2.2 Charts Library

- Sử dụng **Recharts** (`npm install recharts`) — nhẹ, React-native, free
- Biểu đồ:
  - Bar chart: sản xuất theo giờ
  - Line chart: trend 7 ngày
  - Pie chart: phân bố đơn theo trạm

### 2.3 API endpoints cần thêm

```python
GET /api/analytics/hourly?date=2026-04-09&station_id=1  # Số đơn theo giờ
GET /api/analytics/trend?days=7                           # Trend 7 ngày (tổng mỗi ngày)
GET /api/analytics/stations-comparison                    # So sánh năng suất trạm
```

### 2.4 Export báo cáo

- Nút "Xuất báo cáo" → download CSV
- Nội dung: danh sách đơn theo filter (ngày, trạm, waybill)
- API: `GET /api/export/csv?date=2026-04-09&station_id=1`

---

## Phase 3: Dual Camera + PIP Mode

**Mục tiêu:** Hiển thị 2 camera cho trạm có `ip_camera_2` configured.

### 3.1 Dual Camera Side-by-Side

- Khi station có `ip_camera_2`, single view tự động chia đôi iframe:
  ```
  ┌──────────────────┬──────────────────┐
  │  Camera 1 (Main)  │  Camera 2 (Sub)   │
  │   Góc rộng         │   Góc gần         │
  └──────────────────┴──────────────────┘
  ```
- MediaMTX path: `station_{id}_cam1` và `station_{id}_cam2`
- Backend cần: thêm stream manager cho cam2, second MediaMTX path
- `database.py`: `ip_camera_2` đã có sẵn trong schema

### 3.2 Picture-in-Picture (PIP) Mode

- Toggle giữa "Dual" và "PIP":
  - **PIP:** Camera 1 chiếm full, Camera 2 small overlay (góc dưới phải)
  - Click vào PIP → swap camera chính/phụ
- Nút toggle ở góc trên phải player

### 3.3 Grid Mode Dual Camera

- Trong overview grid, mỗi tile hiển thị camera chính
- Badge "2 cam" trên tile → biết trạm có camera phụ
- Click tile → single view → thấy dual

### 3.4 Backend Changes (recorder.py + api.py)

- `CameraStreamManager` cần quản lý 2 stream riêng biệt
- MediaMTX path config thêm: `station_{id}_cam1`, `station_{id}_cam2`
- Recording: chỉ record camera chính (cam1), cam2 chỉ live view
- `recorder.py`: không thay đổi (vẫn record 1 stream)
- `api.py`: station payload đã có `ip_camera_2`

---

## Phase 4: System Health Dashboard

**Mục tiêu:** Trang theo dõi sức khỏe hệ thống thời gian thực.

### 4.1 System Status Page

**UI:** Tab/section trong Settings hoặc trang riêng

Widgets:
- **CPU & RAM usage** — `psutil` library
- **Disk I/O** — read/write speed
- **MediaMTX status** — kết nối tới MTX API `/v3/paths/list`, hiển thị paths active
- **FFmpeg processes** — đếm process ffmpeg đang chạy
- **Server uptime** — thời gian từ khi start uvicorn
- **Network** — IP server, subnet, camera reachability

### 4.2 Backend API

```python
GET /api/system/health           # CPU, RAM, disk, uptime
GET /api/system/processes        # FFmpeg processes count + details
GET /api/system/mtx-status       # MediaMTX paths (đã có, enhance)
GET /api/system/network          # IP, subnet, camera ping status
```

Cần thêm dependency: `psutil>=5.9.0`

### 4.3 Auto-Refresh

- Polling mỗi 5 giây khi trang health mở (SSE không cần — thay đổi chậm)
- Visual indicators: 🟢 OK, 🟡 Warning, 🔴 Critical
- Thresholds:
  - CPU > 80% → 🟡, > 95% → 🔴
  - RAM > 85% → 🟡, > 95% → 🔴
  - Disk > 90% → 🔴 (đã có)

---

## Priority Order

```
Phase 1 → Phase 2 → Phase 3 → Phase 4
```

- **Phase 1** là gap lớn nhất — API có sẵn nhưng UI thiếu
- **Phase 2** mang giá trị kinh doanh — quản lý kho cần số liệu
- **Phase 3** nâng cấp UX — chỉ cần khi có trạm 2 camera
- **Phase 4** cho admin/devops — monitoring chuyên nghiệp

---

## Technical Decisions

### Charts Library: Recharts

- Nhẹ (~40KB gzip), React-native, không cần D3 trực tiếp
- Alternative: Chart.js (heavy), Victory (overkill), Nivo (good nhưng ít phổ biến)
- `npm install recharts`

### Process Monitoring: psutil

- Cross-platform (Windows + macOS + Linux)
- CPU, RAM, disk, network, process listing
- Đã có sẵn trong PyInstaller bundle

### Audit Log: SQLite bảng mới

- Không cần thêm dependency
- Lightweight, query nhanh
- Auto-cleanup: giữ 90 ngày, xoá cũ mỗi ngày

### Dual Camera: MediaMTX Multi-Path

- Mỗi camera = 1 RTSP→WebRTC path riêng trong MediaMTX
- MediaMTX hỗ trợ unlimited paths, zero config overhead
- Không cần thêm instance MediaMTX

---

## Versioning

| Phase | Version |
|---|---|
| Phase 1 | v1.8.0 |
| Phase 2 | v1.9.0 |
| Phase 3 | v1.10.0 |
| Phase 4 | v2.0.0 |

Sau khi hoàn thành cả 4 phase → tag **v2.0.0** release.
