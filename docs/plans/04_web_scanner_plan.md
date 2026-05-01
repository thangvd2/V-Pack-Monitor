# Giai đoạn 4.1: Đưa Máy Quét Lên Web & Định hình Kiến trúc Đa Trạm (Multi-Station)

**Status**: DONE — Implemented in v3.x series.

Kế hoạch này giải quyết hai mục tiêu lớn: Loại bỏ hoàn toàn cửa sổ dòng lệnh Terminal đen ngòm để mang lại trải nghiệm chuẩn Web 100%, và định hướng kiến trúc mở rộng khi nhà kho tăng từ 1 lên nhiều trạm đóng hàng.

## 1. Trả lời câu hỏi: "Khi muốn thêm mới 1 vị trí đóng hàng thì sao?"

Việc chuyển máy quét lên Web mở ra cánh cửa cho mô hình **Centralized Server (Khách - Chủ)** cực kỳ chuyên nghiệp:
- **Máy chủ (Backend):** Cài đặt phần mềm V-Pack trên 1 máy tính trung tâm đủ mạnh (PC/Mac/Server). Máy này cắm dây cáp mạng thẳng vào Router.
- **Tại mỗi Bàn đóng hàng (Client):** Chỉ cần trang bị 1 màn hình Tablet hoặc Laptop giá rẻ, mở URL Web (ví dụ: `http://192.168.1.100:3000`).
- **Máy quét:** Cắm USB vào Tablet/Laptop đó.

**Lộ trình mở rộng tương lai (Bản V-Pack Enterprise):**
Sau khi xong Giai đoạn 4.1 này, trong tương lai ta chỉ cần nâng cấp thêm tính năng "Chọn Trạm (Select Station)" ở màn hình Web.
* Database lưu nhiều Cụm Cấu hình Camera `[Station_1_IP, Station_2_IP]`.
* Màn hình A quét mã vạch => Bắn API lên Server báo "Trạm A vừa có mã vận đơn X" => Server kích hoạt FFmpeg chộp Camera A.
* Tuyệt đối không cần mua nhiểu máy vi tính cấu hình cao cho mỗi bàn!

---

## Proposed Changes: Kế hoạch Kỹ thuật Triển khai Ngay bây giờ

Chúng ta sẽ đập bỏ script `main.py` và nhúng toàn bộ năng lực ghi hình FFmpeg vào một con tim duy nhất: Server FastAPI.

### [Component: Web Frontend]

#### [MODIFY] web-ui/src/App.jsx
- Bổ sung **Global Keyboard Listener (useBarcodeScanner hook)**: Bắt toàn bộ thao tác gõ phím. Vì súng bắn mã vạch bản chất là thao tác gõ phím cực nhanh + phím `Enter` ở cuối. Bằng cách đo tốc độ gõ phím, Web có thể phân biệt được đâu là "Súng bắn" và đâu là người dùng tự bấm phím.
- Gửi sự kiện mã vạch (Bắt đầu mã vận đơn mới hoặc mã "STOP") thẳng xuống API thông qua axios, không cần thao tác click chuột.
- Hiển thị Toast Notification hoặc Badge trạng thái: **"Đang ghi hình đơn: XYZ"** màu đỏ nhấp nháy góc màn hình để nhân viên biết súng đã quét ăn.

### [Component: Backend API & Recording Engine]

#### [MODIFY] api.py
- Chuyển logic từ `main.py` vào `api.py`. API sắm vai trò Điều phối Cục bộ (Global Coordinator).
- Thêm Endpoint **POST `/api/scan/start`**:
  - Nhận payload chứa mã vận đơn.
  - Khởi chạy tiến trình `CameraRecorder` dưới nền (Sử dụng luồng BackgroundTask của FastAPI).
- Thêm Endpoint **POST `/api/scan/stop`**:
  - Nhận lệnh ngắt ghi hình (khi người dùng bắn mã "STOP").
  - Tự động đóng tệp FFmpeg và lưu path vào SQLite Database `packing_video`.
- Cập nhật Live View Web API để trả về thêm trạng thái hệ thống: Đang ở Không tải, hay Đang tiến hành Record.
- (Tính năng này đóng vai trò nền tảng vững chắc cho việc thêm `station_id` quản lý nhiều bàn đóng hàng nếu cần mở rộng sau này).

#### [DELETE] main.py
- Xoá bỏ tệp này hoàn toàn làm đơn giản hoá kiến trúc thành 1-Stack duy nhất.

## User Review Required
> [!IMPORTANT]
> **Yêu cầu đánh giá:**
> 1. Súng quét mã vạch của bạn có xuất ra dấu `Enter` (Xuống dòng) sau khi quét xong 1 mã không? Đa số súng (Yoko, Deli, Honeywell...) đều để mặc định là có. Nếu không, máy quét cần được cài đặt có suffix là Enter.
> 2. Việc gộp hết tất cả từ Terminal lên Web (xoá `main.py`) đồng nghĩa với thao tác "cắm Cáp súng quét vào Máy tính chạy Browser (Giao diện)". Bạn có đồng ý với cơ chế UX "chỉ cần mở trình duyệt và bắn súng" không?

Tôi sẽ tạm dừng tại đây để đợi cái gật đầu của bạn trước khi tiến hành code và xoá tàn dư `main.py`. Mời bạn xem Plan!
