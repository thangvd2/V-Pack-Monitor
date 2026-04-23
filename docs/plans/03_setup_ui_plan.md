# Kế hoạch Triển khai Trình cài đặt Giao diện (Setup UI)

**Status**: DONE — Implemented in v3.x series.

Chuyển đổi V-Pack Monitor từ phần mềm cấu hình thủ công qua mã nguồn sang sản phẩm "Production-ready" có cơ chế cấu hình trực quan qua Frontend.

## Quyết định Thiết kế (Đã được phê duyệt)
- **Chấp nhận Breaking Change:** Tự động đồng bộ và loại bỏ cấu trúc hardcode trong `camera_config.py`, chuyển dữ liệu tập trung hoàn toàn vào bảng `system_settings` trong SQLite.
- **Tích hợp Modal Setup:** Frontend sẽ chặn bằng màn hình "Setup Modal" đè lên Dashboard chính nếu phát hiện thiếu cấu hình (ứng dụng dạng SPA).
- **Trải nghiệm Người Dùng (UX):** Giấu thông tin tài khoản `admin` của IP Camera. Người dùng chỉ cần điền IP và Safety Code (dưới đáy Camera Imou).

## Các thay đổi sẽ thực hiện

### 1. Database & Core

#### [MODIFY] `database.py`
- **Thêm bảng:** `system_settings` (`config_key` TEXT PRIMARY KEY, `config_value` TEXT).
- **Hàm hỗ trợ:** `get_setting(key, default)`, `set_settings(dict)`, `get_all_settings()`.
- **Đồng bộ tự động (Migration):** Khi `init_db()` chạy lần đầu sẽ tự động import các cấu hình có sẵn từ `camera_config.py` (như IP, Safety Code) nếu chưa có settings nào.

#### [MODIFY] `main.py`
- Thay vì `import camera_config` trực tiếp, đọc thông qua `database.get_setting()`.
- Tạo cơ chế Dynamic RTSP Link Generator (Tái cấu trúc ghép link RTSP bằng IP_CAMERA và SAFETY_CODE do DB quy định, giấu user 'admin').

### 2. API Backend 

#### [MODIFY] `api.py`
- **GET /api/settings:** Lấy trạng thái cài đặt để khởi tạo Giao diện.
- **POST /api/settings:** Nhận dữ liệu thiết lập từ Trình duyệt (IP, Code, Days, Lense Mode).
- **Restart Stream Engine:** Viết lại hàm khởi tạo `CameraStreamManager` cho phép truyền cấu hình mới. Gọi lệnh khởi động lại Capture OpenCV khi có người bấm LƯU.

### 3. Giao diện (Frontend)

#### [MODIFY] `web-ui/app/page.tsx` & `web-ui/app/components/*`
- Khi load khởi tạo Dashboard, gọi fetch `/api/settings`. 
- Nếu dữ liệu rỗng (IP = rỗng) -> Hiển thị Modal "V-Pack Quick Setup" đen mờ đè lên toàn màn hình (Ngăn người dùng làm việc).
- **Form Setup:**
  - Input: IP Camera (VD: 192.168.x.x)
  - Input: Safety Code (Mật khẩu dưới đáy Imou)
  - Select: Chế độ Camera (Camera góc rộng (1 Mắt) / Camera kép màn hình PIP (2 Mắt))
  - Select: Xoá Video cũ hơn (3/7/15/30 Ngày)
- **Hành vi Nút Submit:** Kiểm tra độ hợp lệ, push dữ liệu lên POST API. Báo Success và đóng Modal, reload Dashboard ngầm.
