# Hướng Dẫn Từng Bước (Cho Team Sales / Triển Khai) - V-Pack Monitor v1.9.0

Tài liệu dành cho nhân viên kinh doanh / kỹ thuật viên đem V-Pack Monitor đi cài đặt tại kho khách hàng.

## Tiền Đề Cần Chuẩn Bị
1. Máy tính PC/Laptop chạy **Windows 10/11** hoặc **macOS** tại mỗi trạm đóng hàng.
2. Súng bắn mã vạch cổng USB (Barcode Scanner).
3. Đã kết nối mạng LAN nội bộ cùng lớp mạng với Camera IP (Khuyên dùng IPC Imou/Dahua).

---

## Bước 1: Cài Đặt Tự Động

### Trên Windows
1. Tải và giải nén `V-Pack-Monitor` vào ổ đĩa (VD: `E:\V-Pack-Monitor`).
2. Nhấn chuột phải vào `install_windows.bat` → **Run as administrator**.
3. Script tự động xử lý: tải Python 3.13, Node.js 22, FFmpeg, MediaMTX, tạo venv, build frontend, mở port tường lửa, tạo shortcut Desktop.

### Trên macOS
1. Tải và giải nén `V-Pack-Monitor`.
2. Mở Terminal, di chuyển vào thư mục vừa giải nén:
```bash
chmod +x install_macos.sh
./install_macos.sh
```
3. Script tự động: kiểm tra Python 3.10+, Node.js, tạo venv, cài thư viện, build frontend.

---

## Bước 2: Khởi Động Phần Mềm

### Windows
Nháy đúp vào biểu tượng **V-Pack Monitor** trên Desktop. Hoặc chạy `start_windows.bat`. Hệ thống khởi động 2 tiến trình:
- **MediaMTX** — WebRTC live view (port 8889)
- **Python API** — Backend ghi hình, quét mã, cloud sync (port 8001)

### macOS
```bash
./start.sh
```

### Docker
```bash
docker-compose up -d
```

Truy cập: `http://localhost:8001`

---

## Bước 3: Đấu Nối Camera với Trạm Đầu Tiên

1. Bấm nút **Cài Đặt Ngay** ở giữa màn hình.
2. Nhập mã PIN mặc định: `08012011`.
3. Điền thông tin trạm và Camera:
   - **Hãng Camera:** Chọn đúng hãng (Imou/Dahua, Tenda, EZVIZ, Tapo).
   - **IP Camera:** Lấy từ modem hoặc app hãng (VD: `192.168.5.18`).
   - **MAC Address (Khuyến khích):** In trên tem đáy Camera (VD: `30:24:50:48:09:38`). Giúp hệ thống tự tìm lại IP khi mạng đổi.
   - **Mật khẩu RTSP:**
     - **Imou/Dahua:** Safety Code (8 ký tự in ở tem đáy Camera).
     - **Tenda:** Mật khẩu tự đặt lúc cài Camera (mặc định `admin123456`).
     - **EZVIZ:** Verification Code (6 ký tự in ở tem đáy Camera).
     - **TP-Link Tapo:** Tạo "Camera Account" trong app Tapo (Advanced Settings), đặt Username `admin` + Password → nhập Password vào đây.
4. Chọn chế độ `SINGLE` → **LƯU TRẠM NÀY**.
5. Camera sẽ lên sóng Live WebRTC! Cắm súng quét mã vạch và bắn đơn đầu tiên.

---

## Bước 4: Thiết Lập Quản Trị (Nâng Cao)

Nhấp nút Settings (bánh răng) góc phải → Nhập PIN `08012011`:
1. **Dọn rác tự động:** Giữ video 10/30 ngày tuỳ ổ cứng.
2. **Cloud Sync:** Kích hoạt Google Drive hoặc S3.
3. **Telegram Bot:** Nhập Bot Token + Chat ID để nhận cảnh báo.

---

## Bước 5: Bàn Giao cho Khách

1. **Bắt đầu đóng:** Quét mã vận đơn → màn hình đỏ nhấp nháy `ĐANG GHI ĐƠN`.
2. **Kết thúc đóng:** Quét mã STOP hoặc nhấn foot switch → lưu file hoàn tất.
3. **Mã PIN:** Dặn chủ kho thay đổi/giữ kỹ mã `08012011`, không cho nhân viên biết.

---

Chúc TEAM chốt Sale trăm đơn! Mọi lỗi lầm xin báo lại với đội kỹ thuật.
