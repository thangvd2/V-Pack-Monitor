# Kế hoạch Triển khai: Hệ thống Camera Đóng hàng TMĐT

**Status**: DONE — Implemented in v3.x series.

Dự án này nhằm xây dựng một hệ thống phần mềm và phần cứng kết hợp để tự động hóa việc ghi hình quá trình đóng gói đơn hàng. Video sẽ được lưu trữ và liên kết trực tiếp với mã vận đơn (Shopee, Lazada, TikTok Shop), giúp shop dễ dàng trích xuất bằng chứng khi có khiếu nại (refund, hoàn hàng hỏng).

## 1. Đề xuất Phần cứng (Phía bạn chuẩn bị)
- **Camera:** Camera độ phân giải cao (2K/4K). Khuyến nghị dùng **Webcam USB (như Logitech Brio 4K)** hoặc các dòng webcam 2K/4K của Rapoo/Hikvision. Webcam USB dễ kết nối và lập trình hơn so với các dòng IP Camera.
- **Giá đỡ:** Arm kẹp bàn hoặc chân đế cao để gắn thẳng camera chiếu từ trên xuống mặt bàn đóng gói.
- **Máy quét mã vạch (Barcode/QR Scanner):** Dạng cắm USB. Loại này thực chất hoạt động như một bàn phím ảo (nhập mã và tự động nhấn Enter).
- **Máy tính:** PC hoặc Laptop chạy tại quầy đóng gói (cần ổ cứng dung lượng lớn, tốt nhất là HDD 1TB-4TB hoặc NAS để lưu trữ video lâu dài).

## 2. Quy trình Hoạt động (Workflow)
1. **Chờ (Idle):** Hệ thống hiển thị camera trực tiếp (Live preview) trên màn hình để nhân viên căn góc.
2. **Kích hoạt:** Nhân viên dùng súng tít quét mã vận đơn trên phiếu giao hàng.
3. **Bắt đầu ghi (Record):** Phần mềm nhận diện mã vận đơn, tạo một file video mới với tên là mã vận đơn (VD: `SPX_VN123456789.mp4`) và bắt đầu ghi hình.
4. **Kết thúc (Stop):** 
   - *Cách 1:* Nhân viên nhấn phím tắt (VD: Phím Space) hoặc click nút trên màn hình.
   - *Cách 2:* Nhân viên quét một "Mã vạch kết thúc" (in sẵn dán trên bàn).
   - *Cách 3:* Tự động ngắt sau X phút.
5. **Lưu trữ & Quản lý:** Video được nén và lưu vào ổ cứng. Thông tin được đưa vào cơ sở dữ liệu để tìm kiếm nhanh theo mã vận đơn, ngày tháng.

## 3. Kiến trúc Công nghệ đề xuất (Tech Stack)

Để hệ thống chạy mượt mà với camera 4K và có giao diện hiện đại, đẹp mắt, tôi đề xuất:

- **Back-end & Xử lý Camera:** `Python` + `OpenCV`.
  - Python rất mạnh trong việc giao tiếp với phần cứng, đọc luồng video 4K từ camera và sử dụng thư viện FFmpeg để nén video hiệu quả.
  - Sử dụng `FastAPI` để làm bộ khung giao tiếp.
- **Cơ sở dữ liệu:** `SQLite` (Đơn giản, lưu thẳng thành 1 file offline, không cần cài đặt database server phức tạp, đủ đáp ứng vài trăm ngàn đơn).
- **Front-end (Giao diện):** `Next.js` (React) kết hợp `TailwindCSS` hoặc Vanilla CSS.
  - Giao diện dạng Web App chạy nội bộ. Cực kỳ đẹp, mượt mà và dễ sử dụng. Giao diện sẽ hiển thị Live View, danh sách video đã quay và ô tìm kiếm.

*(Hệ thống sẽ chạy hoàn toàn Offline trên máy tính tại quầy để đảm bảo tốc độ và bảo mật).*

> [!TIP]
> Việc chia ra Back-end (Python) và Front-end (Web) giúp tận dụng tối đa sức mạnh ghi hình của Python mà vẫn có được giao diện người dùng xịn xò, dễ thao tác của Web.

## 4. User Review Required (Cần bạn phản hồi)

Trước khi chúng ta bắt tay vào code, hãy thảo luận một vài điểm sau để tôi cấu hình cho chuẩn xác nhất:

1. **Bạn dự định dùng hệ điều hành gì tại quầy đóng gói?** (Windows hay macOS? Thường mọi người dùng Windows tại kho, tôi cần biết để viết mã xử lý thư mục lưu trữ cho đúng).
2. **Bạn thích cách Kết thúc ghi hình (Stop) nào nhất?** (Quét mã vạch đặc biệt, bấm phím tắt, bấm chuột, hay dùng bàn đạp chân USB?)
3. **Tuổi thọ lưu trữ:** Bạn muốn video giữ lại trong bao lâu trước khi tự động xoá để giải phóng ổ cứng? (Ví dụ: 30 ngày hay 60 ngày?)
4. **Ngôn ngữ & Công nghệ:** Bạn có đồng ý với đề xuất dùng **Python + Next.js web UI** không? Hay bạn thích làm một ứng dụng Desktop truyền thống hơn (như Python Tkinter/PyQt)?

---

**Kế hoạch tiếp theo:**
Sau khi bạn chốt các câu hỏi trên, chúng ta sẽ bắt đầu khởi tạo dự án. Tôi sẽ hướng dẫn bạn cài đặt môi trường, sau đó tôi sẽ viết mã phần xử lý Camera trước, rồi đến giao diện quản lý.
