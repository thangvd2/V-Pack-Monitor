# Giai đoạn 4.2: Mở Rộng Hệ Sinh Thái (Giả lập, Đa Trạm, Quản lý Lưu trữ)

**Status**: DONE — Implemented in v3.x series.

Bản thiết kế này nhằm đưa V-Pack Monitor từ phần mềm 1-Trạm cục bộ thành phần mềm quy mô Quản lý Doanh nghiệp (Enterprise-ready).

## Cấu trúc hạng mục

### Hạng mục 1: Khu vực Test & Giả lập Máy Quét (Manual Simulator)
*Vấn đề:* Người dùng hiện tại không có máy quét vật lý, việc thử nghiệm quy trình gặp khó khăn.
*Giải pháp:* 
- Xây dựng một khối (Block) hoặc Popup "Developer Tools" trên giao diện Web Dashboard.
- Cung cấp ô Input để gõ Mã vận đơn bằng bàn phím.
- Thiết kế 2 nút Action (Button): **"Bắt đầu (Giả lập Bắn/Enter)"** và nút **"STOP (Kết thúc)"**.
- Giao diện giả lập này sẽ trực tiếp gọi API `/api/scan` hệt như cách súng quét mã vạch lén gọi ghim ở background.

### Hạng mục 2: Tái Khai sinh Kiến trúc Đa Trạm (Multi-Station Mode)
*Vấn đề:* Database hiện tại sử dụng Key-Value `system_settings` dùng chung, dẫn tới việc chỉ theo dõi được duy nhất 1 bàn đóng hàng.
*Cấu trúc lại Database:*
- [NEW] Bảng `stations`:
  - `id` (INTEGER PK)
  - `name` (TEXT) VD: Bàn Gói Hàng Mỹ Phẩm, Bàn Cân Giày dép...
  - `ip_camera_1` (TEXT)
  - `ip_camera_2` (TEXT) - Hỗ trợ camera hãng khác cắm cùng nếu muốn.
  - `safety_code` (TEXT)
  - `camera_mode` (TEXT)
- Rẽ nhánh Backend: Tiến trình FFMpeg (`global_recorder`) sẽ được chuyển từ dạng Singleton (1 cái) sang một Dictionary chứa bộ Nhớ theo Station: `recorders = { 1: CameraRecorder(), 2: CameraRecorder() }`.
- Giao diện Frontend: Có hộp thả (Dropdown) để User (nhân viên) chọn xem Web này đang dùng cho Trạm nào. Khi có lệnh Scan, nó sẽ dập mã `station_id` gửi lên API.

### Hạng mục 3: Trình Quản lý Kho Lưu Trữ (Storage Manager)
*Vấn đề:* Ổ cứng đầy, hệ thống tự động dọn là tốt, nhưng quản lý vẫn cần chủ động xem xét hoặc xoá lập tức dung lượng.
*Giải pháp:*
- Xây dựng API tính tổng dung lượng thư mục `recordings/`.
- Xây dựng API xoá thủ công (Delete) đối với một đơn hàng bất kỳ hoặc Xoá Toàn Bộ.
- Giao diện UI: Thêm 1 góc cài đặt "Storage", hiển thị biểu đồ thanh ngang dung lượng đang chiếm dụng.

---

## Mức độ ưu tiên để Thực thi

Do Hạng mục 2 (Kiến trúc Đa Trạm) đòi hỏi xoá bảng DB cũ và định hình lại Flow gửi dữ liệu từ Frontend, việc này nên được làm Cuối cùng sau khi mọi thứ khác ổn định. 

1. **[Ưu tiên 1]** Làm "Khu vực Test Giả lập" trước để bạn (User) tha hồ sinh video kiểm thử. Ngay trong phiên tới.
2. **[Ưu tiên 2]** Làm "Trình Quản lý Storage" để thao tác UI quen thuộc với các Video vừa test.
3. **[Ưu tiên 3]** Nâng cấp lõi Database lên Multi-Station.

> [!CAUTION]
> **User Review:** Bạn có đồng ý với thứ tự ưu tiên (1 -> 2 -> 3) này để triển khai code không? Cứ mỗi chặng hái quả xong, bạn sẽ test trực tiếp được luôn!
