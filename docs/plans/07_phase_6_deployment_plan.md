# Bản Thiết Kế Triển Khai Thương Mại: V-Pack Monitor (Giai đoạn 6)

Triết lý của giai đoạn này là thay đổi hoàn toàn cách chúng ta coi V-Pack Monitor là một "Mã Nguồn Của Lập Trình Viên" sang một "Sản Phẩm Đóng Gói Hoàn Chỉnh". Chúng ta sẽ thực hiện 2 tiêu chuẩn triển khai tốt nhất cho khách hàng.

## 1. Phương án Ưu Tiên: Trọn Gói Windows Kịch Bản (The Bootstrap Script)
Đây là tập lệnh thần thánh `install_windows.bat` mà chỉ cần khách hàng nhấn đúp chuột (Run as Administrator), nó sẽ làm mọi thứ thay con người. Phù hợp 90% đối tượng khách hàng kho xưởng!

**Chìa Khoá Khắc Phục Lỗi Máy Khách:**
- **Không đụng chạm Hệ thống:** Nếu trên máy khách không có `FFmpeg`, script sẽ tự tải `ffmpeg.zip` bản siêu nhẹ gốc từ Github bằng `curl`, giải nén bằng `PowerShell`, và đẩy vào thư mục `bin/` ngay trong phần mềm. Khi chạy quay video, V-Pack sẽ lấy FFmpeg cục bộ ở đây thay vì FFmpeg của máy tính!
- **Môi Trường Cách Ly (Virtual Environment):** Sẽ tự tạo thư mục `venv` để tiêm các thư viện `fastapi`, `opencv` vào. Rút USB xoá thư mục đi là máy tính khách sạch bong y như cũ.
- **Tự động cấu hình FireWall:** Xin cấp quyền Admin để mở khe cửa mạng LAN `Port 8001`, cho phép Súng quét mã vạch không dây truy cập vào máy tính chủ.
- **Tạo Lối tắt (Shortcut):** Dùng lệnh tạo File Shortcut `V-Pack Monitor.lnk` quăng thẳng ra màn hình Desktop. Logo ứng dụng sẽ được gắn vào (có thể dùng icon mặc định của Windows nếu chưa có logo).

**Quy trình sử dụng cho End-user:**
1. Khách hàng Right-Click `install_windows.bat` > Run As Admin (Làm đúng 1 lần trong đời).
2. Tới giờ làm việc, khách ra Desktop nhấp đúp cái biểu tượng `V-Pack Monitor`, hệ thống tự bật!

## 2. Phương án Dự Phòng: Trọn Gói Container (Docker Compose)
Dành cho các hệ thống máy chủ, khách hàng nội bộ hoặc máy Mac/Linux không muốn cài lung tung.

- **Dockerfile:** Kết hợp `python:3.11-slim` (nền tảng) + `ffmpeg` (quay video) + `libgl1-mesa-glx` (để hỗ trợ thư viện OpenCV cốt lõi).
- Nhúng toàn bộ mã nguồn và thư mục web rút gọn (`web-ui/dist`) vào lõi hình ảnh (Image).
- Cấu hình `recordings/` và `vpack.db` thành Volumes độc lập (để khi xoá Docker hay cập nhật Phiên bản Phần mềm mới, dữ liệu Lịch sử và Video cũ vẫn nằm yên trên máy).
- Khi bàn giao cho team IT của hãng giao vận, chỉ việc quăng cho họ file `docker-compose.yml` có 10 dòng!

## Câu Hỏi Xác Nhận Nóng (Mời Quản Kho Duyệt)
1. Trong kịch bản Windows, bạn có muốn tôi viết luôn lệnh Tự Mở Trình Duyệt Toàn Màn Hình (Kiosk Mode) trên trình duyệt Chrome hệt như một app Độc lập mỗi khi khách mở `start.bat` không? Hay cứ để nó bay vào tab ẩn danh bình thường của trình duyệt trên máy khách?
2. Kịch bản cài Python `install_windows.bat`: Đoạn đầu script, nếu phát hiện máy khách chưa có Python gốc, tôi sẽ kêu Script tự động tải bộ cài Python từ file EXE chính chủ về tự chạy nền. Bạn ưng chứ?
