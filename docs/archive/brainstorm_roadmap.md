> [!WARNING]
> **⚠️ OUTDATED — Post-v2.1.0 brainstorm. Most items implemented in v2.2-v3.5. Kept for historical reference.**

# Brainstorm — Hướng Phát Triển Tiếp Theo (Post v2.1.0)

> **Ngày:** 2026-04-10
> **Trạng thái:** Đề xuất — chờ VDT đánh giá và chọn ưu tiên

---

## 🎯 Nhóm 1: Ổn Định & Sẵn Sàng Production

### 1.1 Fix Windows Compatibility
- **File:** `docs/windows_fixes_needed.md` đã document chi tiết
- **Vấn đề:** `ping -c` trên Windows, `build.py` thiếu hidden imports
- **Effort:** Thấp — ~15 phút trên máy Windows

### 1.2 Automated Testing
- **Vấn đề:** Hiện tại 0 test. Mỗi lần refactor sợ regression.
- **Đề xuất:**
  - Unit test cho `auth.py` (JWT generate/verify, bcrypt hash/verify)
  - Unit test cho `database.py` (CRUD operations, audit log cleanup)
  - Integration test cho API endpoints (pytest + httpx + TestClient)
  - Frontend component test (vitest + React Testing Library)
- **Effort:** Trung bình

### 1.3 Structured Logging
- **Vấn đề:** 40+ `print()` rải rác, không trace được khi có issue trên production.
- **Đề xuất:**
  - Python `logging` module với file rotation (`RotatingFileHandler`)
  - Log levels: DEBUG / INFO / WARNING / ERROR
  - Log format: `[TIMESTAMP] [LEVEL] [MODULE] message`
  - Log file: `logs/vpack_YYYY-MM-DD.log`, rotate 10MB, giữ 30 ngày
  - Frontend console → structured `console.log` với prefix
- **Effort:** Trung bình

### 1.4 Database Migration / Schema Versioning
- **Vấn đề:** Hiện dùng `CREATE TABLE IF NOT EXISTS`, không handle schema change khi upgrade version.
- **Đề xuất:**
  - Option A: Alembic (overkill cho SQLite nhỏ)
  - Option B: Tự viết migration trong `database.py` — `PRAGMA user_version` + migration steps
  - Mỗi schema change bump version, chạy migration trên startup
- **Effort:** Trung bình

### 1.5 Backup/Restore Database
- **Vấn đề:** Kho mất disk/corrupt DB → mất toàn bộ lịch sử ghi hình. Cần backup định kỳ.
- **Đề xuất:**
  - API endpoint: `POST /api/system/backup` — export SQLite file + metadata JSON
  - API endpoint: `POST /api/system/restore` — import từ file backup
  - Auto-backup: Mỗi ngày 1 lần, giữ 7 bản gần nhất
  - Backup location: `backups/` folder hoặc cloud
  - UI: Nút Backup/Restore trong System Health page (ADMIN only)
- **Effort:** Trung bình

---

## 🚀 Nhóm 2: Features Mới

### 2.1 Auto-Cleanup Old Recordings
- **Vấn đề:** Disk đầy theo thời gian. Video cũ chiếm space nhưng DB record vẫn giữ.
- **Đề xuất:**
  - Setting: Retention period (ví dụ: 30/60/90 ngày)
  - Cron job: Mỗi ngày check video files > retention → xóa file + update DB status = "ARCHIVED"
  - Giữ DB record để tra cứu metadata, chỉ xóa file vật lý
  - UI: Setting trong SetupModal để config retention period
- **Effort:** Thấp

### 2.2 Video Thumbnail Generation
- **Vấn đề:** Grid/History chỉ có icon, khó nhận diện video nhanh.
- **Đề xuất:**
  - FFmpeg extract frame tại 1s: `ffmpeg -i video.mp4 -ss 1 -frames:v 1 thumbnail.jpg`
  - Auto-generate khi stop recording, lưu cùng folder video
  - API trả thêm `thumbnail_url` trong record response
  - Grid/History hiển thị thumbnail thay vì icon
- **Effort:** Thấp-Trung bình

### 2.3 Shift Management (Phân Ca Làm Việc)
- **Vấn đề:** Kho thường có ca sáng/chiều. Cần thống kê năng suất theo ca.
- **Đề xuất:**
  - Admin define ca: Tên, giờ bắt đầu, giờ kết thúc (ví dụ: Ca Sáng 7:00-12:00, Ca Chiều 13:00-17:30)
  - Operator auto-assign ca khi login (dựa giờ hiện tại)
  - Dashboard filter theo ca
  - Report: So sánh năng suất giữa các ca
- **Effort:** Trung bình-Cao

### 2.4 Mobile Responsive UI
- **Vấn đề:** Quản lý muốn xem kho từ xa trên điện thoại/tablet. Hiện UI chỉ desktop.
- **Đề xuất:**
  - Responsive grid: 1 column trên mobile, 2 trên tablet
  - Bottom nav bar trên mobile (thay vì sidebar)
  - Touch-friendly: Button lớn hơn, swipe gestures
  - Camera live view: Auto-fit mobile screen
- **Effort:** Trung bình

### 2.5 Keyboard Shortcuts
- **Vấn đề:** Operator quét mã liên tục, cần thao tác nhanh.
- **Đề xuất:**
  - `Ctrl+L`: Toggle live view
  - `Ctrl+G`: Toggle grid
  - `Ctrl+D`: Toggle dashboard
  - `Escape`: Close modal / back to station selection
  - `Space`: Pause/resume video playback
  - Hiển thị shortcut hint trong UI
- **Effort:** Thấp

### 2.6 Dark Mode
- **Vấn đề:** Kho thường ánh sáng yếu, giảm mỏi mắt.
- **Đề xuất:**
  - CSS variables cho theme colors
  - Toggle button trong header
  - Persist preference trong localStorage
  - Auto-detect system preference (prefers-color-scheme)
- **Effort:** Trung bình

### 2.7 Export PDF Report
- **Vấn đề:** Dashboard chỉ xem web, sếp cần file gửi email.
- **Đề xuất:**
  - jsPDF hoặc html2pdf.js để generate PDF từ dashboard
  - Report template: Header (logo, date range), Charts, Summary table
  - API endpoint: `GET /api/analytics/report?from=&to=&format=pdf`
- **Effort:** Trung bình

---

## 🔗 Nhóm 3: Tích Hợp & Mở Rộng

### 3.1 Tích Hợp API Shopee / TikTok Shop
- **Vấn đề:** Operator phải quét mã thủ công. Nếu tự sync từ đơn hàng → nhanh hơn, ít sai sót.
- **Đề xuất:**
  - Shopee Open API: Lấy order detail, tracking number
  - TikTok Shop API: Tương tự
  - Workflow: Đơn mới → tự động tạo waybill trong V-Pack → Operator chỉ cần chọn đơn
  - Cần OAuth token management, refresh token
- **Effort:** Cao

### 3.2 REST API Token cho Bên Thứ 3
- **Vấn đề:** Kho lớn đã có ERP/WMS, cần hook vào V-Pack để đồng bộ.
- **Đề xuất:**
  - API Key management: Admin tạo/revoke keys
  - Rate limiting per key
  - Webhook config: Đăng ký URL nhận event khi có recording mới
  - Events: `recording.started`, `recording.completed`, `recording.failed`
- **Effort:** Trung bình-Cao

### 3.3 Webhook Notifications
- **Vấn đề:** Tự động hóa workflow thay vì chỉ Telegram.
- **Đề xuất:**
  - Config webhook URL trong settings
  - Events: recording completed, system error, disk almost full
  - Retry logic: 3 lần với backoff
  - Payload: JSON với event type + data
- **Effort:** Thấp-Trung bình

---

## 🛠 Nhóm 4: DevOps & Performance

### 4.1 Docker Hóa Hoàn Chỉnh
- **Vấn đề:** Deploy nhanh cho nhiều kho, không cần install Python/Node trên mỗi máy.
- **Đề xuất:**
  - Multi-stage Dockerfile: Build frontend → Python runtime
  - `docker-compose.yml`: api + mediamtx + volume mounts
  - Environment variables cho config
  - Health check endpoints
- **Effort:** Trung bình

### 4.2 Dashboard Lazy Loading
- **Vấn đề:** Bundle 701KB vì Recharts (~160KB gzip). Chỉ load khi user vào Dashboard.
- **Đề xuất:**
  - `React.lazy(() => import('./Dashboard'))` + `Suspense`
  - Giảm initial load ~160KB
  - Tương tự cho SystemHealth, UserManagement
- **Effort:** Thấp

### 4.3 CI/CD Pipeline
- **Vấn đề:** Build manual, dễ quên step (version bump, zip, release).
- **Đề xuất:**
  - GitHub Actions: Lint → Test → Build → Release
  - Trigger on tag push `v*`
  - Auto-create GitHub release với zip asset
- **Effort:** Trung bình

---

## 📊 Ma Trận Ưu Tiên (Gợi Ý)

| Ưu tiên | Feature | Impact | Effort | Ghi chú |
|---|---|---|---|---|
| 🥇 | 1.5 Backup/Restore DB | Cao — bảo vệ dữ liệu | TB | Production phải có |
| 🥈 | 2.1 Auto-Cleanup Recordings | Cao — disk đầy = die | Thấp | Quick win |
| 🥉 | 1.3 Structured Logging | Cao — debug production | TB | Hỗ trợ hỗ trợ khách hàng |
| 4 | 2.3 Shift Management | Cao — business value | TC | Kho nào cũng cần |
| 5 | 2.4 Mobile Responsive | Cao — UX leap | TB | Quản lý xem từ xa |
| 6 | 2.2 Video Thumbnail | TB — UX tốt hơn | T | Nice to have |
| 7 | 4.2 Dashboard Lazy Loading | TB — performance | Thấp | Quick win |
| 8 | 1.4 DB Schema Migration | TB — future-proof | TB | Cần trước khi scale |
| 9 | 2.7 Export PDF Report | TB — business reporting | TB | Sếp cần |
| 10 | 4.1 Docker | TB — deploy nhanh | TB | Multi-kho |
| 11 | 2.5 Keyboard Shortcuts | Thấp — UX minor | Thấp | Quick win |
| 12 | 2.6 Dark Mode | Thấp — nice to have | TB | Có thể gộp vào v3.x |
| 13 | 3.1 Shopee/TikTok API | Cao — automation | Cao | Research trước |
| 14 | 3.2 API Token cho bên 3 | TB — mở rộng | TC | Enterprise feature |
| 15 | 3.3 Webhook Notifications | TB — automation | T | Gộp với 3.2 |
| 16 | 4.3 CI/CD Pipeline | TB — dev productivity | TB | Hỗ trợ dev |
