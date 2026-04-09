# Lịch Sử Cập Nhật & Phát Hành (Release Notes)

> **Tác giả:** VDT - Vũ Đức Thắng | [GitHub](https://github.com/thangvd2)

## [v1.10.0] - 2026-04-09 (Dual Camera + PIP Mode)

### 📹 Tính Năng Lớn
- **Dual Camera Side-by-Side:** Trạm có 2 camera → hiển thị song song 50/50. Toggle "1 Cam / Dual / PIP".
- **Picture-in-Picture (PIP):** Camera 1 chiếm full, Camera 2 small overlay góc dưới phải.
- **MediaMTX Dual Path:** Backend tự tạo path `station_{id}_cam2` cho camera phụ. Live view WebRTC riêng biệt.
- **Grid Badge:** Ô grid hiển thị badge "2 CAM" cho trạm có camera phụ.

### 🏗️ Kiến Trúc
- **`api.py`**: `CameraStreamManager` quản lý cam2_url riêng. `_mtx_add_path` hỗ trợ suffix. Endpoint `GET /api/live-cam2`.
- **`App.jsx`**: `cameraMode` state ('single-cam' | 'dual' | 'pip'). Conditional render iframe cho dual/PIP. Toggle 3 nút chỉ hiện khi hasCam2.

---

## [v1.9.0] - 2026-04-09 (Dashboard & Analytics Pro)

### 📊 Tính Năng Lớn
- **Dashboard Page:** Trang tổng quan với biểu đồ sản xuất, xu hướng, so sánh trạm. Toggle bằng nút BarChart3 ở header.
- **Biểu Đồ Sản Xuất Theo Giờ:** BarChart (Recharts) hiển thị số đơn theo từng giờ (0-23h). Filter theo ngày và trạm.
- **Xu Hướng 7 Ngày:** LineChart hiển thị trend sản xuất 7 ngày gần nhất.
- **So Sánh Trạm:** PieChart (donut) so sánh năng suất các trạm trong ngày.
- **Xuất CSV:** Download báo cáo danh sách đơn theo filter (ngày, trạm) dạng CSV.

### 🏗️ Kiến Trúc
- **`Dashboard.jsx`** (mới): Component dashboard với Recharts (BarChart, LineChart, PieChart).
- **`database.py`**: 4 hàm analytics mới (get_hourly_stats, get_daily_trend, get_stations_comparison, get_records_for_export).
- **`api.py`**: 4 endpoints mới (`GET /api/analytics/hourly`, `GET /api/analytics/trend`, `GET /api/analytics/stations-comparison`, `GET /api/export/csv`).
- **Recharts** (`npm install recharts`): Thư viện biểu đồ React (~160KB gzip).

---

## [v1.8.0] - 2026-04-09 (User Management UI + Security)

### 👤 Tính Năng Lớn
- **User Management Modal:** Giao diện quản lý user chuyên nghiệp với 3 tab (Người dùng, Phiên hoạt động, Nhật ký hệ thống). ADMIN tạo/sửa/khoá/xoá user trực tiếp từ UI.
- **Đổi Mật Khẩu:** Dropdown user → "Đổi mật khẩu". Xác thực mật khẩu cũ, validate độ dài, confirm match.
- **Audit Log:** Ghi lại mọi hành động quan trọng (LOGIN, LOGOUT, START_RECORD, STOP_RECORD, CREATE_USER, DELETE_USER, CHANGE_PASSWORD, FORCE_END_SESSION). Tự động dọn log cũ sau 90 ngày.
- **Session Management:** Xem tất cả phiên đang active (user, trạm, thời gian). ADMIN có thể force-kick session.

### 🏗️ Kiến Trúc
- **`database.py`**: Thêm bảng `audit_log`, 5 hàm mới (log_audit, get_audit_logs, get_active_sessions, get_session_by_id, end_session_by_id).
- **`api.py`**: 4 endpoints mới (`PUT /api/auth/change-password`, `GET /api/sessions/active`, `DELETE /api/sessions/{id}`, `GET /api/audit-logs`). Audit logging trên 10 action points.
- **`UserManagementModal.jsx`** (mới): 638 dòng, 3-tab UI với CRUD user, session viewer, audit log viewer.
- **`App.jsx`**: Users button (ADMIN-only), user dropdown với đổi mật khẩu, modal integration.

---

## [v1.7.0] - 2026-04-09 (Multi-Camera Live View UI)

### 🖥️ Tính Năng Lớn
- **Overview Grid Mode:** Hiển thị tất cả camera trạm đồng thời trong lưới responsive. Tự động tính số cột dựa trên số trạm (2x2, 3x2, v.v.). Click vào ô → zoom sang single view.
- **View Mode Toggle:** Nút chuyển đổi giữa Single View và Overview Grid ở header (chỉ hiện khi có ≥2 trạm).
- **Click-to-Zoom:** Click ô grid → chuyển sang single view cho trạm đó. Nút "Tổng quan" để quay lại grid.
- **Per-Station Status:** Theo dõi trạng thái ghi hình riêng cho từng trạm trong grid — badge RECORDING/PROCESSING/SẴN SÀNG trên mỗi ô.

### 🎨 UI/UX
- Grid responsive: mobile 1 cột, tablet 2 cột, desktop auto-fill.
- Hover effect trên grid tile: scale + border highlight.
- Barcode simulator ẩn trong grid mode (chỉ hiện ở single mode).
- Station selector ẩn trong grid mode.
- SSE subscribe tất cả trạm trong grid mode — realtime status update.

---

## [v1.6.0] - 2026-04-09 (User Management & Access Control)

### 🔐 Tính Năng Lớn
- **JWT Authentication:** Hệ thống đăng nhập bằng Username/Password với JWT token (PyJWT). Token hết hạn sau 8 giờ (1 ca làm việc), leeway 30s cho đồng hồ LAN không đồng bộ.
- **Role-Based Access Control (RBAC):** Hai vai trò ADMIN (toàn quyền) và OPERATOR (chỉ ghi đơn/xem lịch sử). Tự động ẩn/hiển các nút chức năng theo vai trò.
- **Session Locking:** Acquire/Heartbeat/Release session khi quét mã vạch. Ngăn nhiều người dùng cùng ghi trên 1 trạm. Session tự expire khi server khởi động lại.
- **User Management (ADMIN):** CRUD người dùng đầy đủ — tạo, sửa tên/vai trò/trạng thái, xoá. API được bảo vệ bởi `require_admin` dependency.
- **Auto-create Admin:** Lần đầu khởi động, tự động tạo tài khoản `admin` / mật khẩu `08012011`. Không cần setup thủ công.

### 🗑 Xóa Bỏ
- **PIN System hoàn toàn:** Xóa PinModal, `/api/verify-pin`, mã PIN ở SetupModal. Thay thế bằng user/password login.
- `PinModal.jsx` không còn được import (file vẫn tồn tại để tham khảo).

### 🎨 UI/UX
- **Login Form:** Giao diện đăng nhập glassmorphism với username/password, lỗi hiển thị inline. Conditional render — không dùng react-router.
- **User Info Header:** Hiển thị tên người dùng + vai trò + nút đăng xuất ở header.
- **Role-based UI:** Nút Cloud Sync, Settings, Add Station, Delete Record chỉ hiện cho ADMIN. OPERATOR chỉ thấy giao diện ghi đơn và xem lịch sử.
- **Auto-logout on 401:** Axios interceptor tự động đăng xuất khi token hết hạn hoặc không hợp lệ.

### 🏗️ Kiến Trúc
- **`auth.py`** (mới): JWT token creation/verification, bcrypt password hashing, `get_current_user()` và `require_admin()` FastAPI dependencies.
- **`database.py`**: Thêm bảng `users` (username, password_hash, role, full_name, is_active) và `sessions` (user_id, station_id, started_at, last_heartbeat, status). 13 hàm auth/session mới.
- **`api.py`**: Auth endpoints (login/me/logout), user CRUD (ADMIN only), session locking (acquire/heartbeat/release), RBAC protection trên TẤT CẢ endpoints.
- **`requirements.txt`**: Thêm `PyJWT>=2.8.0`, `passlib[bcrypt]>=1.7.4`.

### 🐛 Sửa Lỗi
- **OPERATOR 401 bug fix:** `checkSettings()` không còn gọi trên mount — chỉ gọi khi mở SetupModal (ADMIN-gated). Tránh OPERATOR bị logout do 401 từ `/api/settings` (ADMIN-only).

---

## [v1.5.0] - 2026-04-09 (Video Pipeline Reliability)

### 🚀 Tính Năng Lớn
- **100% Video Guarantee:** Đảm bảo mọi video ghi hình đều được tracking từ lúc bắt đầu. DB record tạo TRƯỚC khi FFmpeg start, không bao giờ mất dấu video dù server crash.
- **VideoWorker (Background Queue):** Tách luồng xử lý video ra khỏi barcode scanning. Operator quét STOP → trạm giải phóng ngay lập tức → VideoWorker xử lý convert/verify ở background. Operator không bao giờ bị block.
- **Pre-flight Checks:** Trước khi ghi, kiểm tra tự động: ổ cứng còn đủ ≥500MB, FFmpeg còn hoạt động, trạm không đang ghi/đang xử lý. Từ chối ghi nếu điều kiện không đủ.
- **Post-processing Verify:** Sau khi convert .ts→.mp4, dùng FFprobe verify file hợp lệ (duration > 0, codec valid). Video lỗi → mark FAILED + cảnh báo Telegram ngay lập tức.
- **Crash Recovery:** Khi server khởi động lại, tự động detect records bị treo (RECORDING/PROCESSING). Nếu file .ts còn → convert sang MP4. Nếu mất hoàn toàn → mark FAILED + cảnh báo Telegram.
- **SSE Realtime Updates:** Thay thế polling bằng Server-Sent Events. Frontend nhận push ngay khi status thay đổi (RECORDING → PROCESSING → READY/FAILED). Giảm ~1800 requests/giờ.

### 🎨 UI/UX
- **Status Badges:** Mỗi thẻ lịch sử hiển thị badge trạng thái: 🔴 RECORDING, 🟡 PROCESSING, 🟢 READY, ❌ FAILED.
- **Live View Overlay:** Badge "ĐANG XỬ LÝ VIDEO" (amber) hiển thị khi video đang convert.
- **Video Playback Guard:** Disable nút play cho video chưa xử lý xong (RECORDING/PROCESSING).

### 🏗️ Kiến Trúc
- **`video_worker.py`** (mới): ThreadPoolExecutor(max_workers=1), sequential processing, no race conditions.
- **`database.py`**: Thêm `status` column, `create_record()`, `update_record_status()`, `get_pending_records()`.
- **`recorder.py`**: Xóa fallback rename .ts→.mp4 (tránh tạo file invalid khi convert fail).
- **`api.py`**: SSE endpoint `/api/events`, pre-flight checks, crash recovery, handle_scan rewrite.

### 📋 Telegram Alerts
- File mất hoàn toàn → FAILED → cảnh báo Telegram ngay.
- Convert thất bại → FAILED → cảnh báo Telegram ngay.
- Recovery thất bại sau crash → cảnh báo Telegram ngay.
- Recovery thành công / server crash / recording dừng → không cảnh báo (không cần).

---

## [v1.4.0] - 2026-04-09 (WebRTC + Recording Overhaul)

### 🚀 Tính Năng Lớn
- **WebRTC Live View qua MediaMTX:** Thay thế toàn bộ MJPEG/OpenCV pipeline bằng MediaMTX + WebRTC. Live view giờ dùng sub-stream H.264 (640x352) remux trực tiếp qua MediaMTX → browser decode bằng hardware. Độ trễ gần như thời gian thực (~200ms), CPU server gần như 0.
- **MPEG-TS Safe Recording:** Ghi hình dưới dạng MPEG-TS (streamable, không corrupt khi mất điện/sập process). Khi dừng ghi, tự động convert sang MP4 với `-movflags +faststart`.
- **GPU Hardware Transcode:** Auto-detect GPU encoder (Intel QSV, NVIDIA NVENC, AMD AMF, Apple VideoToolbox) để transcode HEVC→H.264 khi lưu video. Fallback `libx264 ultrafast` nếu không có GPU.
- **Async Video Saving:** Quá trình lưu video chạy trên thread riêng, không block barcode scanning. Frontend hiển thị trạng thái "Đang lưu video..." và tự refresh khi xong.
- **Double-stop Protection:** `_stop_lock` + `_stopping_recorders` dict ngăn race condition khi nhiều scan request trigger concurrent `stop_recording()`.

### ✨ Cải Tiến
- **Video Player Pro rewrite:** Progress bar với seek, time display, volume, playback speed (0.5x-2x), keyboard shortcuts (Space, arrows, Esc), auto-hide controls, snapshot, download.
- **Frontend status badges:** Green (idle), red pulse (recording), amber pulse (saving).
- **`install_windows.bat` rewrite:** Auto-install Python 3.13.3 + Node.js v22 LTS + FFmpeg + MediaMTX, tạo firewall rule, desktop shortcut. Dùng `goto` labels thay vì nested `if/else`.
- **`start_windows.bat` rewrite:** Khởi động MediaMTX + Python server, mở Chrome Kiosk mode. Kill chính xác process (port-based), không kill tất cả python.exe.
- **`start.sh` update (macOS):** Khởi động MediaMTX + FFmpeg PATH + proper cleanup.
- **`.gitignore` update:** Thêm `bin/`, `hls/`, `install_log.txt`.

### 🗑 Xóa Bỏ
- Loại bỏ dependency OpenCV (`cv2`) khỏi backend — live view không còn dùng OpenCV.
- Loại bỏ MJPEG multipart streaming pipeline.
- Loại bỏ FLV.js, HLS.js (đã thử và không phù hợp bằng WebRTC).

### 📋 Yêu cầu mới
- **MediaMTX** (`bin/mediamtx/mediamtx.exe`): Media server proxy RTSP→WebRTC. Tự động download bởi `install_windows.bat`.

---

## [v1.3.2] - 2026-04-08 (macOS + Windows Fix)

### 🚀 Tính Năng Mới
- **macOS 1-click installer**: Double-click `Install V-Pack Monitor.command` → tự động cài tất cả. Double-click `Start V-Pack Monitor.command` → khởi động server + mở trình duyệt.
- **`install_macos.sh`**: Script cài đặt tự động qua Terminal — check Python 3.10+, Node.js, tạo venv, pip install, build frontend.

### ✨ Cải Tiến
- **Dockerfile**: Python 3.10 → 3.14 (tương thích `str | None` syntax).
- **README.md**: Version v1.3.2, thêm hướng dẫn macOS + Docker, fix lệnh `python api.py` → `uvicorn`.
- **README_SETUP.md**: Version v1.3.2, thêm hướng dẫn macOS + Docker + MAC Address.

### 🐛 Sửa Lỗi
- **Windows install_windows.bat**: Cửa sổ chớp tắt khi `python` không trong PATH — thêm fallback sang `py` launcher, error handling + `pause` ở mọi nhánh lỗi.
- **Windows start_windows.bat**: Thêm check venv tồn tại trước khi activate, thông báo lỗi rõ ràng nếu chưa cài đặt.

---

## [v1.3.1] - 2026-04-08 (Auto-Discovery Update)

### 🚀 Tính Năng Mới
- **Tự Động Tìm Lại Camera (Auto-Discovery by MAC)**: Khi camera đổi IP do sự cố mạng/DHCP reset, hệ thống tự động quét LAN theo MAC Address, cập nhật IP mới và reconnect — không cần can thiệp tay.
- **Nút "Quét IP" trong Cài Đặt**: Nhập MAC Address (in trên tem đáy camera) → bấm quét → tìm ngay IP mới.
- **Badge trạng thái reconnect**: Hiển thị "Đang tìm lại Camera..." / "Đã tìm thấy IP mới" trên camera preview.
- **Công cụ test RTSP** (`test_rtsp.py`): Script kiểm tra nhanh kết nối RTSP camera theo IP + Safety Code, hỗ trợ tất cả brand.

### ✨ Cải Tiến
- Upgrade Python runtime từ 3.9 → **3.14** (hiệu năng, bảo mật).
- Sửa lỗi phát hiện subnet LAN (`192.168.5.x` thay vì fallback sai `192.168.1.x`).
- Sửa lỗi parse MAC Address có octet thiếu số 0 (VD: `30:24:50:48:9:38`).
- Tắt OpenCV warning spam khi camera offline.
- `start.sh` cleanup: `kill -9` + signal trap, `source venv/bin/activate`.
- Thêm `pyTelegramBotAPI` vào `requirements.txt`.

---

## [v1.3.0] - 2026-04-08 (Premium Release)

Gói nâng cấp "Premium Features" tập trung nâng cao khả năng quản trị, phòng ngừa rủi ro và tăng cường tốc độ xử lý khiếu nại cho nhân viên đóng hàng.

### 🚀 Những Thay Đổi Lớn (Major Features)
- **Cảnh Báo Ổ Cứng Hết Chỗ (Disk Health Alerts)**: Hệ thống làm mới tự động quét dữ liệu thư mục ghi hình. Thanh Progress bar chuyển đỏ và nháy liên tục khi cảnh báo dung lượng thực tế trống dưới 10%, nhằm ngăn ngừa lỗi không thể ghi đè Video.
- **Tích hợp Chatbot Telegram Trực Tiếp (Two-way Comms)**: Cấu hình linh hoạt qua UI Modal (Token, Chat ID). Phân luồng Cảnh báo "Lỗi đứt gãy Cloud Sync" tự động văng vào máy chủ. Hỗ trợ lệnh Listen Control trên Mobile Chat: gọi `/baocao` báo cáo năng suất ngày, gọi `/kiemtra` hiển thị danh sách thiết bị.
- **Nâng Cấp Video Player Pro**: Trình xem lại vận đơn nhúng gọn gàng trong Modal (Pop-up), loại bỏ sự phiền phức mở Tab mới. Trang bị tốc độ tua nhanh 2.0x, và chế tạo công cụ "Chụp Hình - Snapshot", xuất khẩu bằng chứng khung hình thành JPG lưu nhanh chóng.

### ✨ Cải Tiến (Improvements)
- Hỗ trợ đầy đủ luồng Camera RTPS đến từ các thiết bị `Tenda`, `TP-Link Tapo`, `EzViz`, song hành với `Imou` và `Dahua` truyền thống.
- **Production Build All-in-one**: Hỗ trợ xuất xưởng (Export) trực tiếp toàn bộ Backend + UI thành một file nhị phân duy nhất `.exe`/`.app` cực gọn với `PyInstaller` và Script kịch bản cài đặt `inno_setup`. Cạy mở sự hiện diện "như một phần mềm thực sự", không cần lệnh mở cmd.

### 🧹 Code Hygiene (Dọn dẹp mã nguồn)
- Chuẩn hoá toàn bộ Linter rules PEP8 (chặn Warning) qua các file lõi SQL và Backend.
- Tối ưu luồng tiến trình (Daemon thread) để nhốt trình lắng nghe Telegram an toàn song song cạnh Event Loop WebSocket FastAPI.
- Xóa bỏ rác Code và các comment lỗi thời.

---

## [v1.2.0] - 2026-04-05 (Cloud Sync Update)
- Bổ sung luồng kết nối Google Drive & S3.
- ...

## [v1.1.0] - Giao Diện Barcode Scanner UI
- Ra mắt công cụ quét mã vạch chuyên dụng và Trạm thu thập Multi-Station, phân chia logic xử lý nhiều Camera.

## [v1.0.0] - Bản Nguyên Góc
- MVP API Video MP4 bằng OpenCV. Hỗ trợ 1 Camera duy nhất.
