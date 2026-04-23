# Báo cáo Đánh giá và Đề xuất Tối ưu Hệ thống V-Pack

**Status**: DONE — Implemented in v3.x series.

Hệ thống cơ bản đã hoạt động trơn tru. Tuy nhiên để chạy ổn định trong kho bãi 24/7 với vài ngàn đơn hàng/ngày, tôi đã kiểm tra lại toàn bộ source code và phát hiện một số **"Nút thắt cổ chai" (Bottlenecks)** cần được tối ưu hóa như sau:

## 1. Tối ưu Luồng Video Kép (Camera Overload) - **Quan trọng nhất 🚨**
**Hiện trạng:** Ở file `api.py`, hàm `generate_frames()` mở cục bộ một kết nối RTSP `cv2.VideoCapture(RTSP_URL)` riêng tư mỗi khi có 1 người mở trang Live View.
- **Vấn đề:** Nếu bạn mở Dashboard trên 3 máy tính (hoặc điện thoại), phần mềm sẽ tạo ra 3 luồng lấy video từ Camera. Các dòng Camera IP dân dụng (Imou/Ezviz) thường sẽ bị treo hoặc văng mạng nếu có trên 2-4 luồng RTSP cùng lúc.
- **Giải pháp:** Cần tái cấu trúc lại luồng Live thành 1 **Background Thread (Luồng nền)** duy nhất lấy video từ Camera, và "chia sẻ" (Broadcast) khung hình đó ra cho hàng tá máy con xem Live cùng lúc. 

## 2. Truy vấn Database bị chậm theo thời gian
**Hiện trạng (`database.py` & `api.py`):** 
- Hàm `get_records` đang gọi lệnh SQLite `SELECT ...` lấy toàn bộ DB, sau đó dùng thuật toán `for` của Python để lọc `search` (Search Memory).
- Front-end Fetch Auto-refresh lại Database mỗi 5 giây.
- **Vấn đề:** Nếu sau 1 tháng bạn có 10,000 đơn hàng, mỗi 5 giây website sẽ tải cục data khổng lồ, và Python sẽ cực kì lag.
- **Giải pháp:** 
  1. Xử lý tìm kiếm bằng SQLite `LIKE %search%` ở Backend (Tối ưu Memory).
  2. Bổ sung `LIMIT 50` hoặc `LIMIT 100` khi xem danh sách.
  3. Sử dụng Dependency Management/Context `with sqlite3.connect` cho an toàn luồng dữ liệu.

## 3. Tối ưu Hiệu Năng Ghép Hình (Cross-platform Hardware Acceleration)
**Hiện trạng (`recorder.py`):** 
Chế độ số 3 (Picture in Picture) đang dùng FFmpeg với codec `libx264`, sử dụng CPU bằng vi xử lý mềm (`-preset ultrafast`).
- **Vấn đề:** Tốn khá nhiều nhân CPU trên cả máy Mac và Windows khi mở liên tục 24/7.
- **Giải pháp:** Viết thêm hàm cơ chế **Tự động nhận diện Hệ điều hành (Auto-detect OS)** trong `recorder.py`:
  - **Trên macOS**: Hệ thống tự động chuyển mã (codec) sang `h264_videotoolbox` để tối ưu hóa với chip Apple Silicon/Intel.
  - **Trên Windows**: Hệ thống tự động dò tìm phần cứng và kích hoạt `h264_nvenc` (Card màn hình NVIDIA) hoặc `h264_qsv` (Vi xử lý Intel QuickSync).
  => Đảm bảo máy tính chạy PIP ghép hình luôn mát mẻ và giữ mức CPU ~0% trên mọi nền tảng!

## 4. Quản lý Quỹ Đạo Ổ Cứng (Storage Aging)
- Việc quay camera 2K/4K/1080p liên tục và ngắt theo mã đơn sẽ gây đầy bộ nhớ Macbook sau 1-2 tuần.
- **Giải pháp:** Cần viết thêm 1 hàm background job (Cronjob hoặc Background Task trong FastAPI) tự động xóa các file video & dữ liệu quá X ngày (ví dụ quá 7 ngày).

---

## Ý kiến của bạn (Reiew Required)

> [!TIP]
> **Các tính năng trên không khó để nâng cấp**. Tuy nhiên tôi cần bạn xác nhận:
> 1. Bạn muốn giải quyết TẤT CẢ nút thắt trên, hay chỉ ưu tiên cái nào trước? (Khuyến nghị: Mục 1 và 2 là tối quan trọng).
> 2. Có cần làm tính năng tự động xoá video (Mục 4) luôn không, và bạn muốn giữ file lại bao nhiêu ngày?
