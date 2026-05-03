# Hướng Dẫn Từng Bước (Cho Team Sales / Triển Khai) - V-Pack Monitor v3.5.0

Tài liệu dành cho nhân viên kinh doanh / kỹ thuật viên đem V-Pack Monitor đi cài đặt tại kho khách hàng.

## Tiền Đề Cần Chuẩn Bị
1. Máy tính PC/Laptop chạy **Windows 10/11** hoặc **macOS** tại mỗi trạm đóng hàng. Vui lòng tham khảo cấu hình máy và thiết bị mạng chi tiết tại **[HARDWARE_REQUIREMENTS.md](docs/HARDWARE_REQUIREMENTS.md)**.
2. Súng bắn mã vạch cổng USB (Barcode Scanner).
3. Đã kết nối mạng LAN nội bộ cùng lớp mạng với Camera IP (Khuyên dùng IPC Imou/Dahua).

---

## Bước 1: Cài Đặt Tự Động

### Trên Windows
1. Tải và giải nén `V-Pack-Monitor` vào ổ đĩa (VD: `E:\V-Pack-Monitor`).
2. Nhấn chuột phải vào `scripts/install_windows.bat` → **Run as administrator**.
3. Script tự động xử lý: tải Python 3.13, Node.js 22, FFmpeg, MediaMTX, tạo venv, build frontend, mở port tường lửa, tạo shortcut Desktop.

### Trên macOS
1. Tải và giải nén `V-Pack-Monitor`.
2. Mở Terminal, di chuyển vào thư mục vừa giải nén:
```bash
chmod +x scripts/install_macos.sh
./scripts/install_macos.sh
```
3. Script tự động: kiểm tra Python 3.10+, Node.js, tạo venv, cài thư viện, build frontend.

---

## Bước 2: Khởi Động Phần Mềm

### Windows
Nháy đúp vào biểu tượng **V-Pack Monitor** trên Desktop. Hoặc chạy `scripts/start_windows.bat`. Hệ thống khởi động 2 tiến trình:
- **MediaMTX** — WebRTC live view (port 8889)
- **Python API** — Backend ghi hình, quét mã, cloud sync (port 8001)

### macOS
```bash
./scripts/start.sh
```

### Docker
```bash
docker-compose up -d
```

Truy cập: `http://localhost:8001`

---

## Bước 3: Đăng Nhập & Đấu Nối Camera

1. Mở trình duyệt, đăng nhập bằng tài khoản mặc định: Username `admin` / Mật khẩu `08012011`.
2. Bấm nút **Cài Đặt Ngay** ở giữa màn hình.
3. Điền thông tin trạm và Camera:
   - **Hãng Camera:** Chọn đúng hãng (Imou/Dahua, Tenda, EZVIZ, Tapo).
   - **IP Camera:** Lấy từ modem hoặc app hãng (VD: `192.168.5.18`).
   - **MAC Address (Khuyến khích):** In trên tem đáy Camera (VD: `30:24:50:48:09:38`). Giúp hệ thống tự tìm lại IP khi mạng đổi.
   - **Mật khẩu RTSP:**
     - **Imou/Dahua:** Safety Code (8 ký tự in ở tem đáy Camera).
     - **Tenda:** Mật khẩu tự đặt lúc cài Camera (mặc định `admin123456`).
     - **EZVIZ:** Verification Code (6 ký tự in ở tem đáy Camera).
     - **TP-Link Tapo:** Tạo "Camera Account" trong app Tapo (Advanced Settings), đặt Username `admin` + Password → nhập Password vào đây.
4. Chọn chế độ ghi hình (chọn **Rec: 1080p** cho Main-stream hoặc **Rec: 480p** cho Sub-stream) → Bấm **LƯU TRẠM NÀY**.
5. Camera sẽ lên sóng Live WebRTC! Cắm súng quét mã vạch và bắn đơn đầu tiên.

---

## Bước 4: Thiết Lập Quản Trị (Nâng Cao)

Từ v3.4.0, giao diện ADMIN được chia làm 2 tab: `📹 Vận hành` và `📊 Tổng quan`. Hãy chuyển sang tab **Tổng quan** để truy cập các cài đặt hệ thống.

Nhấp nút **Settings** (bánh răng) ở góc phải:
1. **Dọn rác tự động:** Giữ video 10/30 ngày tuỳ ổ cứng.
2. **Cloud Sync Scheduler:** Kích hoạt Google Drive hoặc S3 và đặt lịch đồng bộ tự động hàng ngày (ví dụ: 02:00 sáng).
3. **Telegram Bot:** Nhập Bot Token + Chat ID để nhận cảnh báo khi trạm mất kết nối.

### Quản lý Người dùng
Trong User dropdown (Click vào tên Admin góc phải trên cùng):
1. Chọn **Người dùng**: Thêm tài khoản cho nhân viên đóng hàng (OPERATOR) → chỉ được ghi đơn & xem lịch sử.
2. Chọn **Đổi mật khẩu** để cập nhật bảo mật tài khoản.
3. Chọn **Nhật ký Hệ thống**: Xem Audit Log lưu trữ lịch sử thao tác của tất cả user.

### Giám sát Hệ thống (System Health)
Nằm ngay trong tab **Tổng quan**:
- Giám sát CPU / RAM / Disk usage thời gian thực.
- Quản lý các tiến trình FFmpeg đang chạy.
- **Camera Health Monitoring**: Khung trạng thái cho biết camera nào đang Online/Offline, kèm theo báo động chớp viền đỏ nếu camera mất kết nối.

---

## Bước 5: Bàn Giao cho Khách

1. **Bắt đầu đóng:** Quét mã vận đơn. Hệ thống phát ra **tiếng bíp đi lên** và màn hình hiện badge đỏ `ĐANG ĐÓNG HÀNG`.
2. **Kết thúc đóng:** 
   - Quét mã kiện tiếp theo để tự động đóng kiện cũ, HOẶC quét mã STOP. 
   - Hệ thống phát **tiếng bíp đi xuống** và video được xử lý.
   - Nếu muốn hủy ghi video hiện tại (không lưu), quét mã **EXIT**.
3. **Lưu ý Auto-stop (10 phút):** Mỗi đơn hàng bị giới hạn 10 phút ghi hình. Ở phút thứ 9, máy tính sẽ **đổ chuông cảnh báo (beep liên tục)** để nhắc nhân viên quét mã. Quá 10 phút video tự dừng để giải phóng tài nguyên.
4. **Bảo mật:** Dặn chủ kho đổi mật khẩu `admin` ngay sau khi nhận, tạo tài khoản OPERATOR cho nhân viên.

---

## Tính Năng Tự Động (v3.5.0)

Giải thích cho khách hàng về các tính năng chạy nền tự động của hệ thống:
- **Tự động tìm lại camera:** Khi router cấp lại IP mới cho camera, hệ thống dùng MAC Address để quét mạng nội bộ và lấy IP mới tự động.
- **Tự động dọn ổ cứng:** Tuân thủ theo số ngày lưu trữ trong Cài đặt chung, hệ thống quét và xoá video cũ mỗi giờ.
- **Khôi phục SSE (Auto-reconnect):** Màn hình hiển thị live nếu rớt mạng nội bộ sẽ tự động kết nối lại và nạp lại dữ liệu (chống treo màn hình).
- **Phát hiện Camera Mất Nguồn:** Nếu camera offline quá 5 phút, Telegram tự báo tin nhắn để khách hàng kiểm tra nguồn và cáp mạng.

---

Chúc TEAM chốt Sale trăm đơn! Mọi lỗi lầm xin báo lại với đội kỹ thuật.
