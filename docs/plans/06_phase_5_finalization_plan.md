# Kế hoạch Hoàn thiện V-Pack Monitor (Giai đoạn 5)

Kế hoạch này nhắm tới việc hoàn thiện các lỗ hổng cuối cùng về bảo mật quản trị, cung cấp cái nhìn tổng quan về năng suất, và chuẩn bị sẵn sàng để chuyển giao phần mềm cho End-User (Chủ Kho) mà không cần họ phải biết code.

## 1. Bảo mật & Chống phá hoại (Security)
Bảo vệ tính toàn vẹn của dữ liệu lưu trữ, ngăn chặn nhân viên đóng hàng vô tình hoặc cố ý xóa video/thay đổi cài đặt Camera.

### Thay đổi Backend
- **Tích hợp mã PIN:** Lưu `ADMIN_PIN` vào hệ thống `system_settings` (Mặc định: `1234321` hoặc `1234`).
- **Xác thực:** Tạo API `POST /api/verify-pin` để kiểm tra mã PIN.

### Thay đổi Frontend
- **PinGate UI:** Tạo Component Nhập PIN (như màn hình khoá điện thoại).
- Mật khẩu sẽ được yêu cầu khi:
  - Bấm vào biểu tượng **Thùng Rác** xoá video.
  - Bấm vào nút **Cài Đặt Hệ Thống / Cài Đặt Trạm**.
- Khóa session trong phiên hiện tại (nếu đã nhập đúng PIN 1 lần thì không cần nhập lại cho đến khi F5 trang).

## 2. Widget Thống kê Năng suất (Analytics)
Cung cấp cái nhìn tổng quan nhanh về năng suất gói hàng trong kho xưởng theo từng ngày.

### Thay đổi Backend
- Tạo API `GET /api/analytics/today`.
- Logic SQL: Chạy query đếm `COUNT(id)` các video được ghi nhận trong chu kỳ ngày hôm nay (`recorded_at >= DATE('now')`) chia theo từng Trạm.

### Thay đổi Frontend
- Thêm một khối giao diện (Widget) nhỏ gọn ở màn hình chính, hoặc hiển thị ngay bên dưới hộp Dropdown chọn trạm.
- Nội dung hiển thị: 
  - Tổng đơn toàn kho đi được trong ngày: (Ví dụ: 1,234 đơn)
  - Số đơn của Trạm đang chọn: (Ví dụ: 300 đơn)

## 3. Kiến trúc Đóng gói (Packaging & Production Build)
Chuyển đổi dự án từ chế độ "Phát triển" (Dùng 2 Terminal, 1 cho Python, 1 cho Vite React) thành 1 khối duy nhất dễ bề cài đặt.

### Tích hợp React vào FastAPI (Single Server)
Chạy lệnh `npm run build` để xuất giao diện web ra file HTML/JS tĩnh.
Cấu hình FastAPI `api.py` tự động host thư mục Frontend build. Thay vì mở port `3001` cho web và `8001` cho api, chúng ta chỉ cần ĐÚNG 1 port `8001`.

### Khôi phục `main.py` làm Start Script
- Xây dựng lại file bash/bat `start.bat` (Windows) & `start.sh` (Mac) chỉ với hành động:
  - Chạy `python -m uvicorn api:app --port 8001`
  - Tự động mở trình duyệt `http://localhost:8001`

> [!TIP]
> Việc Build React và nhúng thẳng vào FastAPI giúp ứng dụng chạy cực nhẹ, không cần cài đặt NodeJS rườm rà trên máy chủ của kho xưởng. 

## Câu Hỏi Xác Nhận (Open Questions)
1. Bạn có muốn cấu hình Admin PIN Mặc định là số mấy không? (Thường là `123456` hoặc tuỳ chọn).
2. Việc hiển thị số lượng đơn nên được đặt ngay cạnh thanh Tiêu đề V-Pack Monitor bên trên, hay nằm ở khu vực Cột Danh sách Lịch sử bên phải? Mời Quản đốc chia sẻ ý kiến thẩm mỹ.
