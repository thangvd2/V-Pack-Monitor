# Lịch Sử Cập Nhật & Phát Hành (Release Notes)

> **Tác giả:** VDT - Vũ Đức Thắng | [GitHub](https://github.com/thangvd2)

## [v1.3.2] - 2026-04-08 (Windows Fix)

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
