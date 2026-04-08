# 📦 V-Pack Monitor (CamDongHang) - v1.3.0

Hệ thống giám sát đóng hàng và lưu trữ tự động tối ưu hóa cho nền tảng thương mại điện tử (Shopee, TikTok, Lazada). Giải pháp cung cấp hệ thống quản lý Camera trạm đóng gói, ghi hình chính xác theo kiện hàng và cung cấp bằng chứng "Thép" giúp xử lý khiếu nại trong 1 nốt nhạc.

![V-Pack Monitor Architecture](/placeholder.png "Mô phỏng Hệ thống")

## 🌟 Chức năng nổi bật (v1.3.0 Premium)
- 📹 **Record Đa Trạm (Multi-Station):** Hỗ trợ nhiều trạm đóng hàng, cấu hình riêng biệt cho từng bàn đóng với mã PIN/Safety Code. Hỗ trợ nhiều hãng Camera như Imou, Dahua, Tenda, Tapo, Ezviz, v.v.
- 🎯 **Quét Mã Vạch (Smart Barcode):** Tự động bám theo vận đơn. Cục diện Camera chỉ Record khi bắt đầu gói mã kiện hàng, và tự kết thúc Video khi quét mã EXIT hoặc kiện tiếp theo.
- ☁️ **Đồng Bộ Hoá Điện Toán Đám Mây (Cloud Sync):** Backup dữ liệu hàng ngày lên ổ đĩa Google Drive hoặc kho lưu trữ S3 (MinIO, AWS) nhằm tránh mọi mất mát rủi ro phần cứng ở kho.
- 🤖 **Telegram Bot 2 Chiều:**
  - *Báo Cáo Tức Thì:* Gửi cảnh báo về điện thoại ngay khi lưu trữ Cloud bị lỗi, hay ổ cứng SSD trong kho có nguy cơ sập báo đầy.
  - *Chatbot Tra Cứu:* Gõ lệnh `/baocao` hoặc `/kiemtra` trên Telegram, Bot sẽ tự động trích xuất sản lượng gói hàng trong ngày kèm dung lượng ổ cứng rảnh.
- 🎬 **Video Player Pro:** Khung xem Video hỗ trợ tua 0.5x, 1x, 1.5x, 2x nhanh chóng. Đặc biệt công cụ "Snapshot" bắt trọn vẹn khung hình rõ nét tải ngay tức khắc, giảm tải áp lực cho Call Center.

## 🚀 Hướng Dẫn Cài Đặt (Dành cho Developer)

**Yêu cầu hệ thống:** Python 3.9+ & Node.js 18+

#### 1. Khởi động Giao diện (Frontend)
```bash
cd web-ui
npm install
npm run dev
```

#### 2. Khởi động Máy chủ lõi (Backend)
```bash
# Cài đặt môi trường ảo
python3 -m venv venv
source venv/bin/activate  # Hoặc venv\Scripts\activate.bat với Windows

pip install -r requirements.txt
python api.py
```
> Trạm điều khiển API sẽ khởi chạy ở cổng `:8001`.

> [!TIP]
> **Dành riêng cho người dùng Windows:** Thư mục mã nguồn đã có sẵn các file tự động hoá. Bạn không cần gõ lệnh thủ công mà chỉ cần:
> 1. Click đúp vào `install_windows.bat` ở lần đầu tiên để vòng lặp tự tải thư viện.
> 2. Click đúp vào `start_windows.bat` cho các lần sử dụng hàng ngày để máy tự động mở Server Backend và Giao diện Web cùng lúc.

## 📦 Biên dịch Ứng dụng Thành Phẩm (Production Executable)
Nếu bạn muốn tạo file cài đặt cho máy tính Khách hàng (End-user) mà không cần cài Python/Node, vui lòng dùng công cụ `build.py`:
```bash
python build.py
```
*(Yêu cầu đã cài PyInstaller)*

Kết quả sẽ sinh ra tệp `V-Pack-Monitor.exe` (Trên Windows) hoặc `V-Pack-Monitor` (Trên MacOS) chứa toàn khối Logic C++ và giao diện React bọc kin đáo. Để tạo bộ cài đặt chuyên sâu trên Windows, vui lòng nạp file `inno_setup.iss` vào phần mềm **Inno Setup**.

## 👥 Cấu hình Lần Đầu (Onboarding)
- **Truy cập web UI**: http://localhost:5173 (Môi trường Dev) hoặc mở giao diện app Exe (Môi trường Pro).
- **Mã PIN quản trị viên:** `08012011`
- **Kết nối Bot Telegram:** Vào mục cấu hình, nhập `Bot Token` và `Chat ID`. Mọi thông tin sẽ được mã hoá bảo mật.

## 🛠 Troubleshooting (Các Lỗi Thường Gặp)
**Q: Trình duyệt không load được API Camera RTSP?**
A: Phải cấp luồng truy cập UDP (Port 554) ở Modem Wifi mạng nội bộ. Đồng thời kiểm tra *Safety Code* (mã an toàn ở vỏ đáy Camera) đã nhập đúng trên Web chưa.

**Q: Cài đặt Cloud Google Drive đòi JSON, lấy ở đâu?**
A: Đăng ký Google Cloud Console -> Tạo Service Account -> Export định dạng JSON.

## 📜 Giấy phép
Copyright (c) 2024-2026 **VDT - Vũ Đức Thắng**. All rights reserved.

Phần mềm V-Pack Monitor là tài sản trí tuệ của tác giả **VDT (Vũ Đức Thắng)**. Nghiêm cấm mọi hành vi sao chép, phân phối, hoặc sử dụng lại mã nguồn mà không có sự đồng ý bằng văn bản từ tác giả.

Xem chi tiết tại file [LICENSE](./LICENSE).

## 👤 Tác giả

**VDT - Vũ Đức Thắng**
- GitHub: [https://github.com/thangvd2](https://github.com/thangvd2)
- Dự án: [V-Pack Monitor](https://github.com/thangvd2/V-Pack-Monitor)
