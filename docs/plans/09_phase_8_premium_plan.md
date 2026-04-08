# Kế Hoạch Triển Khai Giai Đoạn 8: Premium Features & Stability

Giai đoạn 8 tập trung vào việc gia tăng tính ổn định cấp doanh nghiệp (Enterprise), các tiện ích cho chủ kho và công cụ Playback nâng cao cho việc truy xuất bằng chứng. 

## Tính năng 1: Cảnh báo "Bình Xăng" Ổ Cứng (Disk Health Dashboard)

Tính năng này giúp báo động đỏ cho chủ kho khi ổ cứng máy tính C: hoặc D: đã gần hết chỗ lưu video, ngăn chặn rủi ro mất video.

### Backend (`api.py`)
- Thêm đường dẫn (Endpoint) `GET /api/system/disk`.
- Sử dụng hàm `shutil.disk_usage("recordings")` của thư viện Python tiêu chuẩn. Hàm này hoàn toàn tương thích chéo (cross-platform), hoạt động tốt trên cả MacOS (statvfs) và Windows (GetDiskFreeSpace), đảm bảo báo cáo dung lượng chính xác trên mọi thiết bị.

### Frontend (`web-ui`)
- Hiển thị một thanh Progress Bar góc trên cùng màn hình (Phần Header).
- Trạng thái bình thường: Màu Xanh / Vàng.
- Nếu dung lượng trống `< 10%` (> 90% Đã dùng): Thanh cảnh báo chuyển sang Đỏ rực kèm dòng chữ nhấp nháy `Cảnh Báo: Ổ Cứng Sắp Đầy!`.

---

## Tính năng 2: Thông Báo Telegram Tự Động (Telegram Bot)

Hỗ trợ gửi báo cáo hàng ngày (VD: cuối ngày) và gửi tin nhắn khẩn cấp khi Cloud lưu trữ gặp vấn đề mạng.

### Theo dõi Cấu hình (`database.py` & `SetupModal.jsx`)
- Thêm key `TELEGRAM_BOT_TOKEN` và `TELEGRAM_CHAT_ID` vào bảng Settings.
- Bổ sung Form nhập thiết lập Telegram trong cửa sổ Cài Đặt Chung (SetupModal).

### Backend Tích Hợp (`api.py` & `cloud_sync.py`)
- Viết module `telegram_bot.py` hỗ trợ hàm `send_telegram_message(text)`.
- Gửi tin nhắn **Báo Cáo (Report)**: Khi người dùng truy cập Dashboard hoặc hệ thống theo dõi ngầm. (Tạm thời tích hợp Nút "Gửi báo cáo ngay" để test + 1 luồng Background nhỏ check giờ lúc 18h).
- Gửi tin nhắn **Cảnh Báo (Alert)**: Khi `cloud_sync.py` đẩy file Google Drive bị lỗi mạng.

---

## Tính năng 3: Công Cụ Video (Playback Speed & Snapshot)

Biến trình xem Video trên Web trở nên Pro hơn để cắt ngắn thao tác của nhân viên CSKH Shopee/Tiktok.

### Frontend (`web-ui/src/App.jsx`)
- Gắn thanh công cụ bên dưới khung phát Video.
- **Tốc độ phát (Speed):** Gọi thẳng vào thuộc tính `videoElement.playbackRate`. Cung cấp nút `0.5x`, `1x`, `2x`.
- **Trích xuất ảnh (Snapshot):** Khi user bấm "Chụp", lấy thẻ `<video>` nhúng thẳng vào một Canvas tàng hình `ctx.drawImage()`, rồi xuất ra dạng Base64 (PNG), kích hoạt trigger cho Trình duyệt tự tải bức ảnh đó xuống với tên `[Ma_Van_Don]_snapshot.png`. 

---

## Tính năng 4: Nâng Cấp Đóng Gói (Production Packaging)

Tránh sự thiếu chuyên nghiệp và rủi ro từ hộp đen CMD của các file `.bat` và `.vbs`, chúng ta sẽ nâng cấp cơ chế đóng gói (Packaging) dành cho đối tượng End-User trên Windows.

### Kỹ thuật Đóng Gói "All-in-One":
1. **PyInstaller Build (`.exe`):**
   - Đóng gói toàn bộ mã nguồn Python (`api.py`, Backend, Web UI assets) vào một file duy nhất: `V-Pack-Monitor.exe` sử dụng PyInstaller với cờ `--noconsole` (không tự mở hộp thoại dòng lệnh).
   - Khách hàng KHÔNG cần phải cài đặt sẵn Python nữa. Mọi thứ được nhúng cố định.
2. **WinSW / NSSM làm Windows Service (Tuỳ chọn cho Auto-Restart):**
   - File `V-Pack-Monitor.exe` sẽ được bọc lại để cài làm một "Windows Service" đích thực, giúp nó khởi động cùng hệ điều hành, vô hình hoàn toàn và tự động Restart nếu có lỗi.
3. **Inno Setup (Bộ Cài Đặt):**
   - Thay vì nén file `.zip`, chúng ta có thể biên dịch thành một trình Cài Đặt `Setup.exe`. Trình cài đặt sẽ tự copy file vào `C:\Program Files\V-Pack`, tự thiết lập Firewall, tự đăng ký tự động Service chạy ngầm. Khách hàng cảm nhận như đang setup một phần mềm chuyên nghiệp.

---

## Mức Độ Ưu Tiên
Chúng ta sẽ chia nhỏ kế hoạch để thực thi.
- **[Bước 1] Thêm API Disk + UI Ổ cứng:** Dễ, làm nền tảng kiểm tra sức khỏe khoẻ.
- **[Bước 2] Thêm bộ sinh Ảnh Snapshot & Speed cho Player:** Hỗ trợ trực tiếp nhân viên đóng hàng.
- **[Bước 3] Tích hợp Telegram & Cài đặt UI:** Báo cáo liên kết cho chủ kho.
- **[Bước 4] PyInstaller & Đóng gói:** Cuối cùng, để cài đặt.

> [!IMPORTANT]
> Tôi đã sửa lại Kế hoạch theo phản hồi của bạn. Nếu bạn Đồng Ý, xin hãy 'Continue' để tôi lên danh sách công việc (`task.md`) và lao vào Code nhé!
