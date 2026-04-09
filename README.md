# 📦 V-Pack Monitor (CamDongHang) - v1.8.0

Hệ thống giám sát đóng hàng và lưu trữ tự động tối ưu hóa cho nền tảng thương mại điện tử (Shopee, TikTok, Lazada). Giải pháp cung cấp hệ thống quản lý Camera trạm đóng gói, ghi hình chính xác theo kiện hàng và cung cấp bằng chứng "Thép" giúp xử lý khiếu nại trong 1 nốt nhạc.

![V-Pack Monitor Architecture](/placeholder.png "Mô phỏng Hệ thống")

## 🌟 Chức năng nổi bật (v1.8.0)
- 📹 **Record Đa Trạm (Multi-Station):** Hỗ trợ nhiều trạm đóng hàng, cấu hình riêng biệt cho từng bàn đóng. Hỗ trợ nhiều hãng Camera như Imou, Dahua, Tenda, Tapo, Ezviz, v.v.
- 🔴 **WebRTC Live View (Sub-second Latency):** Quan sát trực tiếp qua WebRTC với độ trễ gần như thời gian thực, chất lượng H.264 gốc từ camera. Không decode/re-encode, CPU server gần như 0.
- 🎯 **Quét Mã Vạch (Smart Barcode):** Tự động bám theo vận đơn. Camera chỉ Record khi bắt đầu gói mã kiện hàng, tự kết thúc Video khi quét mã EXIT hoặc kiện tiếp theo.
- 🎬 **Ghi hình MPEG-TS an toàn:** Record dưới dạng MPEG-TS (streamable), tự động chuyển sang MP4 khi dừng. Hỗ trợ hardware-accelerated transcode HEVC→H.264 (Intel QSV, NVIDIA NVENC, AMD AMF, Apple VideoToolbox).
- ☁️ **Đồng Bộ Hoá Điện Toán Đám Mây (Cloud Sync):** Backup dữ liệu hàng ngày lên Google Drive hoặc S3 (MinIO, AWS).
- 🤖 **Telegram Bot 2 Chiều:** Cảnh báo tức thì + Chatbot tra cứu (`/baocao`, `/kiemtra`).
- 🎬 **Video Player Pro:** Tua 0.5x-2x, Snapshot chụp khung hình JPG.
- 🔍 **Auto-Discovery Camera:** Tự động tìm lại camera khi đổi IP (quét theo MAC Address), không cần can thiệp tay.
- 🔐 **JWT Authentication & RBAC:** Đăng nhập bằng Username/Password. Phân quyền ADMIN (toàn quyền) / OPERATOR (ghi đơn & xem lịch sử). Session locking ngăn xung đột multi-user.
- 🖥️ **Multi-Camera Overview Grid:** Xem tất cả camera cùng lúc trong lưới responsive. Click-to-zoom, per-station status realtime.

## 🏗 Kiến Trúc Hệ Thống (v1.8.0)

```
Camera Imou (RTSP)
    ├─ Main-stream (HEVC 2304x1296) → FFmpeg → MPEG-TS → MP4 (recording)
    └─ Sub-stream  (H.264 640x352)  → MediaMTX → WebRTC → Browser (live view)
```

- **MediaMTX**: Media server proxy RTSP→WebRTC, zero-CPU live view, single binary (~30MB)
- **FFmpeg**: Record + post-process (MPEG-TS safe recording, HEVC→H.264 GPU transcode)
- **FastAPI**: Backend API, station management, barcode scanning, cloud sync
- **React**: Frontend dashboard với WebRTC player, video player, analytics

## 🚀 Cài Đặt Nhanh

### macOS
```bash
chmod +x install_macos.sh
./install_macos.sh
./start.sh
```

### Windows
1. Click đúp `install_windows.bat` (chạy bằng Administrator)
2. Click đúp biểu tượng **V-Pack Monitor** trên Desktop

### Docker
```bash
docker-compose up -d
```

## 🛠 Cài Đặt Thủ Công (Developer)

**Yêu cầu:** Python 3.10+ & Node.js 18+

```bash
# Backend
python3 -m venv venv
source venv/bin/activate        # macOS/Linux
pip install -r requirements.txt

# Frontend
cd web-ui && npm install && npm run build && cd ..

# Khởi động
python -m uvicorn api:app --host 0.0.0.0 --port 8001
```
> Trạm điều khiển API sẽ khởi chạy ở cổng `:8001`.
> MediaMTX WebRTC player ở cổng `:8889`.

> [!TIP]
> **Dành riêng cho người dùng Windows:** Thư mục mã nguồn đã có sẵn các file tự động hoá. Bạn không cần gõ lệnh thủ công mà chỉ cần:
> 1. Click đúp vào `install_windows.bat` ở lần đầu tiên để vòng lặp tự tải thư viện (Python, Node.js, FFmpeg, MediaMTX).
> 2. Click đúp vào `start_windows.bat` cho các lần sử dụng hàng ngày để máy tự động mở Server Backend + MediaMTX + Giao diện Web cùng lúc.

> [!TIP]
> **Dành riêng cho người dùng macOS:** Tương tự Windows, dùng:
> 1. `chmod +x install.sh && ./install.sh` lần đầu.
> 2. `./start.sh` cho các lần sử dụng hàng ngày.

## 📦 Biên dịch Ứng dụng Thành Phẩm (Production Executable)
Nếu bạn muốn tạo file cài đặt cho máy tính Khách hàng (End-user) mà không cần cài Python/Node, vui lòng dùng công cụ `build.py`:
```bash
python build.py
```
*(Yêu cầu đã cài PyInstaller)*

Kết quả sẽ sinh ra tệp `V-Pack-Monitor.exe` (Trên Windows) hoặc `V-Pack-Monitor` (Trên MacOS) chứa toàn bộ logic và giao diện React. Để tạo bộ cài đặt chuyên sâu trên Windows, vui lòng nạp file `inno_setup.iss` vào phần mềm **Inno Setup**.

> [!NOTE]
> Bản build PyInstaller hiện tại chưa bundle MediaMTX. Cần đặt `mediamtx.exe`/`mediamtx` vào thư mục `bin/mediamtx/` bên cạnh executable.

## 👥 Cấu hình Lần Đầu (Onboarding)
- **Truy cập web UI**: http://localhost:5173 (Môi trường Dev) hoặc mở giao diện app Exe (Môi trường Pro).
- **Tài khoản mặc định:** Username `admin` / Mật khẩu `08012011` (tự tạo lần đầu khởi động). Nên đổi mật khẩu ngay sau khi đăng nhập.
- **Quyền hạn:** ADMIN (toàn quyền: cài đặt, cloud sync, quản lý user) / OPERATOR (chỉ ghi đơn & xem lịch sử).
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
