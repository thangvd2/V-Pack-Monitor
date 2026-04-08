# Bản Thiết Kế Giai Đoạn 7: Lưu Trữ Đám Mây (Cloud Backup)

**Mục tiêu:** Ngăn chặn nguy cơ mất bằng chứng video do hư hỏng phần cứng/mất cắp/ổ cứng rác máy chủ. Đẩy các video Lịch Sử lên Đám Mây bằng cơ chế "Kích hoạt bằng tay" (Manual Trigger).

## 1. Cơ Chế Hoạt Động (Manual Upload)
Thay vì dùng tự động hoá ban đêm dễ bị gián đoạn do nhân viên ngắt điện máy chủ để đi về, tác vụ Cloud Tracking giờ đây sẽ do Quản Lý chủ động kiểm soát.
- **Thêm tính năng trên UI:** Trên thanh Header cạnh nút chức năng, thêm biểu tượng ☁️ **"Đẩy dữ liệu lên Cloud"** (Có khoá bảo mật PIN Cấp độ Quản lý).
- **Luồng xử lý:**
  1. Yêu cầu nhập mã Quản Lý (Admin PIN).
  2. Bấm nút, API `POST /api/cloud-sync` được gọi.
  3. Quét toàn bộ video chưa được đánh dấu `synced` (hoặc kiểm kê video ngày hôm qua/nay).
  4. Nén toàn bộ vào 1 file `V-pack_Backup_YYYY_MM_DD.zip` tạm thời (hoặc tải trực tiếp từng file tuỳ thiết lập).
  5. Đẩy thẳng lên Đám Mây. Tải xong, hệ thống thông báo "Đã sao lưu thành công".
  6. **Kết quả:** Giữ nguyên các File Video trên máy để giao diện Web vẫn coi lại bình thường (Không o ép dọn dẹp dung lượng).

## 2. Giải Pháp Cloud (Ưu Tiên Google Drive)
Vì độ phổ biến vượt trội, Google Drive sẽ là cấu hình Mặc Định của hệ thống. Đồng thời hệ thống vẫn cung cấp Option của S3 để tương thích với các kho vận dùng Cloud riêng.

**A. Phương thức Google Drive (Mặc định)**
Hệ thống sử dụng thư viện `google-api-python-client` qua đường **Service Account**. 
Trong phần Cài Đặt (Setup Modal), khách hàng sẽ có luồng tải tệp `credentials.json` (chìa khoá dịch vụ của Google Console). Ứng dụng sẽ tự dùng Robot để uplaod thẳng video từ Server lên Thư mục Google Drive được uỷ quyền. Bạn hoàn toàn không cần cấp quyền Pop-up lằng nhằng như cho người thường.

**B. Phương thức S3-Compatible Storage (Dự Phòng)**
Hỗ trợ giao thức `boto3` nếu khách muốn đồng bộ về AWS / Cloudflare R2 / MinIO nội bộ ở Server tổng.
Người dùng sẽ nạp `ENDPOINT_URL`, `ACCESS_KEY`, `SECRET_KEY`.

--- 
*Bản Kế hoạch này đã được tiếp nhận phản hồi từ Quản đốc (Thao tác Thủ Công, Ưu tiên G-Drive, Không tự xoá video) và đã được cập nhật logic triệt để. Sẵn sàng lưu chuyển vào Thư viện.*
