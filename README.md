# 📦 V-Pack Monitor (CamDongHang) - v1.3.2

Hệ thống giám sát đóng hàng và lưu trữ tự động tối ưu hóa cho nền tảng thương mại điện tử (Shopee, TikTok, Lazada). Giải pháp cung cấp hệ thống quản lý Camera trạm đóng gói, ghi hình chính xác theo kiện hàng và cung cấp bằng chứng "Thép" giúp xử lý khiếu nại trong 1 nốt nhạc.

![V-Pack Monitor Architecture](/placeholder.png "Mô phỏng Hệ thống")

## 🌟 Chức năng nổi bật (v1.3.2)
- 📹 **Record Đa Trạm (Multi-Station):** Hỗ trợ nhiều trạm đóng hàng, cấu hình riêng biệt cho từng bàn đóng với mã PIN/Safety Code. Hỗ trợ nhiều hãng Camera như Imou, Dahua, Tenda, Tapo, Ezviz, v.v.
- 🔄 **Tự Động Tìm Lại Camera (Auto-Discovery):** Khi camera đổi IP do DHCP, hệ thống tự quét LAN theo MAC Address, cập nhật IP mới và reconnect.
- 🎯 **Quét Mã Vạch (Smart Barcode):** Tự động bám theo vận đơn. Camera chỉ Record khi bắt đầu gói mã kiện hàng, tự kết thúc Video khi quét mã EXIT hoặc kiện tiếp theo.
- ☁️ **Đồng Bộ Hoá Đám Mây (Cloud Sync):** Backup dữ liệu hàng ngày lên Google Drive hoặc S3 (MinIO, AWS).
- 🤖 **Telegram Bot 2 Chiều:** Cảnh báo tức thì + Chatbot tra cứu (`/baocao`, `/kiemtra`).
- 🎬 **Video Player Pro:** Tua 0.5x-2x, Snapshot chụp khung hình JPG.

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

## 📜 Giấy phép
Copyright (c) 2024-2026 **VDT - Vũ Đức Thắng**. All rights reserved.

Phần mềm V-Pack Monitor là tài sản trí tuệ của tác giả **VDT (Vũ Đức Thắng)**. Nghiêm cấm mọi hành vi sao chép, phân phối, hoặc sử dụng lại mã nguồn mà không có sự đồng ý bằng văn bản từ tác giả.

Xem chi tiết tại file [LICENSE](./LICENSE).

## 👤 Tác giả

**VDT - Vũ Đức Thắng**
- GitHub: [https://github.com/thangvd2](https://github.com/thangvd2)
- Dự án: [V-Pack Monitor](https://github.com/thangvd2/V-Pack-Monitor)
