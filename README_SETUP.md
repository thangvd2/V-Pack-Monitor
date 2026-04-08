# Hướng Dẫn Từng Bước (Cho Team Sales / Triển Khai) - V-Pack Monitor

Tài liệu này được biên soạn dành cho nhân viên kinh doanh / Kỹ thuật viên đem phần mềm V-Pack Monitor đi cài đặt tại kho của khách hàng. Hãy làm theo hướng dẫn tuần tự dưới đây.

## Tiền Đề Cần Chuẩn Bị
1. Một máy tính PC/Laptop chạy Window 10/11 tại mỗi trạm đóng hàng.
2. Súng bắn mã vạch cổng USB (Barcode Scanner).
3. Đã kết nối mạng LAN nội bộ cùng lớp mạng với Camera IP (Khuyên dùng IPC Imou/Dahua).

## Bước 1: Khởi Tạo Môi Trường Tự Động
1. Tải và giải nén file `V-Pack-Monitor-v1.1.zip` vào ổ đĩa mong muốn trên máy tính (VD: `D:\V-Pack-Monitor`).
2. Mở thư mục vừa giải nén, click đúp chuột vào file `install_windows.bat`.
3. Nhâm nhi một ngụm trà. File lệnh sẽ TỰ ĐỘNG xử lý mọi việc:
   - Tự động tải Python và FFmpeg.
   - Trích xuất và cấu hình Tường Lửa (Mở port 8001 cho máy chủ nội bộ báo mạng).
   - Thiết lập Shortcut biểu tượng phần mềm ngay trên Desktop.

## Bước 2: Khởi Động Phần Mềm
1. Sau khi cài xong, quay ra Desktop và nháy đúp vào biểu tượng **V-Pack Monitor**.
2. File `start_windows.bat` sẽ kích hoạt toàn bộ Hệ thống ngầm và mở Web ở chuẩn *Không viền màn hình (Kiosk Mode)*.
3. Không làm gì cả, màn hình Web tĩnh của Hệ thống sẽ sáng lên sẵn sàng làm việc.

## Bước 3: Đấu Nối Camera với Trạm Đầu Tiên
Hệ thống lên lần đầu sẽ yêu cầu Cài Đặt Trạm. Hãy làm theo các bước:
1. Bấm nút `Cài Đặt Ngay` ở giữa màn hình đen.
2. Bảng cấu hình xuất hiện. **Mã PIN Mặc Định của hệ thống lúc này là:** `08012011`.
3. Điền thông tin Trạm (tên trạm đóng hàng).
4. Khai báo 2 thông tin cốt lõi của Camera:
   - **Hãng Camera:** Chọn đúng hãng thực tế (Imou/Dahua, Tenda, EZVIZ, hay Tapo).
   - **IP Camera:** Xin ở modem Wifi hoặc ứng dụng của hãng trên điện thoại (ví dụ: `192.168.1.55`).
   - **Mật khẩu RTSP:** Tuỳ vào Hãng Camera mà mục này cài đặt khác nhau.
     - **Imou / Dahua:** Nhập `Safety Code` (mã ngẫu nhiên 8 ký tự in ở tem sườn đáy Camera).
     - **Tenda:** Nhập mật khẩu bạn tự đặt lúc cài Camera (mặc định hay dùng là `admin123456`).
     - **EZVIZ:** Nhập `Verification Code` (6 ký tự viết hoa in ở tem dưới đáy Camera).
     - **TP-Link Tapo:** Phải tạo "Camera Account" trong app Tapo (Phần Advanced Settings). Ở đó nhớ phải đặt Username là `admin`, và đặt 1 cái Password, xong mang Password đó nhập vào đây!
5. Cuối cùng, chọn Chế Độ Camera `SINGLE` -> Ấn **LƯU TRẠM NÀY**.
6. Vậy là màn hình Camera sẽ lên sóng Live theo thời gian thực! Bạn có thể cắm súng quét mã vạch và bắn đơn đầu tiên!

## Bước 4: Thiết Lập Quản Trị Hệ Thống (Nâng Cao)
Nhấp vào nút Settings (bánh răng) màu xanh trên góc phải. Nhập PIN `08012011`. Ở đây bạn có thể giúp chủ kho cài:
1. **Dọn rác tự động:** Giữ video trong 10 ngày hay 30 ngày (Ghim tuỳ chọn này tuỳ theo ổ cứng của máy tính bự cỡ nào).
2. **Setup Lên Đám Mây Mây (Cloud Sync):** Kích hoạt Google Drive, paste nguyên xi file Json chữ dài nhằng của Service Account vào, ném ID Folder đích cho nó.

## Bước 5: Bàn Giao & Trainning Cơ Bản cho Khách
1. **Lệnh bắt đầu đóng:** Kêu nhân viên Cầm súng quét tít vào tờ mã vận đơn -> màn hình báo đỏ nhấp nháy chữ `ĐANG GHI ĐƠN`.
2. **Lệnh kết thúc đóng:** Gói hàng xong kêu nhân viên nhấn phím tắt trên bộ đạp chân (Foot switch) hoặc đơn phẻ nhất là... quét 1 mã tạo bằng bộ sinh mã "STOP" riêng biệt để huỷ ngắt Camera lưu File hoàn tất.
3. **Mã Bảo Mật:** Nhớ DẶN KỸ ông Chủ Kho thay đổi/giữ kỹ mã PIN `08012011` kia, nhân viên đóng gói tuyệt đối KHÔNG cho biết mã này để tránh nó tự động bấm Xoá Video ăn trộm hàng.

Chúc TEAM chốt Sale trăm đơn! Mọi lỗi lầm xin báo lại với đội kỹ thuật nòng cốt.
