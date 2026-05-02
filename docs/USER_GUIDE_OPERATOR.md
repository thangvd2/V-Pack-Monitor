Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)

# V-Pack Monitor v3.5.0 — Hướng Dẫn Sử Dụng cho OPERATOR

## Mục Lục

1. [Giới Thiệu](#1-giới-thiệu)
2. [Đăng Nhập](#2-đăng-nhập)
3. [Chọn Trạm Làm Việc](#3-chọn-trạm-làm-việc)
4. [Giao Diện Chính](#4-giao-diện-chính)
5. [Quy Trình Đóng Hàng Hàng Ngày](#5-quy-trình-đóng-hàng-hàng-ngày)
6. [Chế Độ Camera](#6-chế-độ-camera)
7. [Grid Tổng Quan](#7-grid-tổng-quan)
8. [Xem Lại Video](#8-xem-lại-video)
9. [Dashboard Thống Kê](#9-dashboard-thống-kê)
10. [Chuyển Trạm](#10-chuyển-trạm)
11. [Đổi Mật Khẩu](#11-đổi-mật-khẩu)
12. [Đăng Xuất](#12-đăng-xuất)
13. [Khắc Phục Sự Cố Thường Gặp](#13-khắc-phục-sự-cố-thường-gặp)

---

## 1. Giới Thiệu

**V-Pack Monitor** là hệ thống camera ghi hình kho hàng dành cho thương mại điện tử. Mỗi kiện hàng được quay lại trong quá trình đóng gói, giúp bảo vệ cả nhân viên lẫn khách hàng khi có khiếu nại.

**Vai trò OPERATOR** là nhân viên đóng hàng. Bạn sử dụng hệ thống mỗi ngày để quét mã vạch, bật camera ghi hình, và theo dõi quá trình đóng gói từng kiện hàng.

> Bạn không cần lo về cấu hình hệ thống. Việc thêm trạm, quản lý người dùng, cài đặt camera đều do **Administrator** phụ trách.

---

## 2. Đăng Nhập

1. Mở trình duyệt (Chrome, Edge, Firefox).
2. Truy cập địa chỉ: `http://localhost:8001`
3. Nhập **Tên đăng nhập** và **Mật khẩu** do Administrator cấp.
4. Bấm **Đăng Nhập**.

Nếu sai tên hoặc mật khẩu, hệ thống báo "Đăng nhập thất bại". Hãy kiểm tra lại hoặc liên hệ Administrator.

Phiên làm việc tự hết hạn sau **8 giờ**. Khi đó bạn sẽ bị đăng xuất và cần đăng nhập lại.

---

## 3. Chọn Trạm Làm Việc

Sau khi đăng nhập, bạn sẽ thấy màn hình **Chọn Trạm Làm Việc** với lời chào:

> "Xin chào {họ tên}, vui lòng chọn trạm để bắt đầu"

Mỗi trạm hiển thị ở dạng thẻ (card). Trạng thái được cập nhật tự động mỗi 10 giây:

| Trạng thái | Ý nghĩa | Hành động |
|------------|---------|-----------|
| 🟢 **Trống** | Trạm sẵn sàng | Click vào thẻ để chọn |
| 🔴 **Đang dùng** | Ai đó đang sử dụng | Không thể chọn, thẻ bị mờ và khoá |
| Viền vàng + "Phiên của bạn đang giữ trạm này" | Bạn đang giữ trạm | Click để quay lại trạm |

**Cách chọn:**

1. Click vào một trạm có trạng thái 🟢 **Trống**.
2. Hệ thống hiện "Đang kết nối...".
3. Sau khi kết nối thành công, bạn vào giao diện chính.

Nếu màn hình hiện thông báo: "Chưa có trạm nào được cấu hình. Vui lòng liên hệ Administrator", hãy báo cho quản lý hệ thống.

---

## 4. Giao Diện Chính

### 4.1 Thanh Header

Thanh trên cùng chứa các nút và thông tin sau (từ trái sang phải):

| Thành phần | Mô tả |
|------------|-------|
| **Logo "V-Pack Monitor"** | Tên hệ thống |
| **Trạm: {tên}** (dropdown) | Chuyển sang trạm khác |
| **LayoutGrid** | Bật/tắt chế độ Grid tổng quan (chỉ hiện khi có 2+ trạm) |
| **BarChart3** | Mở Dashboard thống kê |
| **Hôm nay: X đơn / Y đơn** | Thống kê nhanh trong ngày |
| **Tìm mã vận đơn...** (Search) | Tìm kiếm bản ghi theo mã vận đơn |
| **Đã Sử Dụng: X GB (Y file)** | Dung lượng ổ cứng đã dùng |
| **Tên user** (dropdown góc phải) | **Đổi mật khẩu** hoặc **Đăng xuất** |

### 4.2 Thanh Cảnh Báo Ổ Cứng

Khi ổ cứng sắp đầy, một thanh màu đỏ nhấp nháy hiện lên với dòng: **"Cảnh Báo: Ổ Cứng Sắp Đầy!"**

Ngay lập tức báo cho Administrator để tránh mất dữ liệu ghi hình.

### 4.3 Vùng Nội Dung

Vùng chính hiển thị một trong ba chế độ:

1. **Camera Live + Lịch sử** (mặc định khi vào hệ thống)
2. **Dashboard** (bấm **BarChart3**)
3. **Grid Tổng quan** (bấm **LayoutGrid**)

---

## 5. Quy Trình Đóng Hàng Hàng Ngày

Đây là quy trình bạn thực hiện mỗi ngày.

### 5.1 Bắt Đầu Ghi Hình

Có hai cách quét mã:

- **Cách 1 (khuyên dùng):** Dùng súng quét mã vạch, quét trực tiếp mã vận đơn trên kiện hàng.
- **Cách 2:** Gõ mã vào ô **Công Cụ Giả Lập**, sau đó bấm **Bắt Đầu Ghi** hoặc nhấn **Enter**.

Sau khi quét thành công:

- Badge chuyển sang 🔴 **"Đang đóng hàng: [MÃ VẠCH]"**
- Camera bắt đầu ghi hình

> **Lưu ý an toàn (Auto-stop):** Mỗi video có thời lượng tối đa là 10 phút. Nếu bạn quên quét mã kiện tiếp theo, hệ thống sẽ tự động dừng ghi và lưu video. Ở phút thứ 9, hệ thống sẽ phát tiếng "beep" liên tục và hiển thị đồng hồ đếm ngược trên màn hình để nhắc nhở.

> Video được ghi dưới dạng MPEG-TS. Dữ liệu được ghi liên tục nên không sợ mất video khi mất điện đột ngột.

### 5.2 Dừng Ghi Hình

Có ba cách dừng:

| Hành động | Kết quả |
|-----------|---------|
| Quét mã vận đơn **tiếp theo** | Tự động chốt đơn hiện tại, bắt đầu ghi đơn mới |
| Quét mã **STOP** | Dừng ghi, **lưu** video |
| Quét mã **EXIT** | Dừng ghi, **bỏ qua** video (không lưu) |

Sau khi dừng, video đi qua các trạng thái:

1. 🔴 **Đang ghi hình** — chưa thể xem lại
2. 🟡 **Đang xử lý** — đang chuyển đổi định dạng video
3. 🟢 **Sẵn sàng** — có thể xem lại

Chờ đến trạng thái **Sẵn sàng** rồi mới phát lại video.

### 5.3 Luồng Công Việc Điển Hình

1. Lấy kiện hàng, quét mã vận đơn. Camera bắt đầu ghi.
2. Tiến hành đóng gói kiện hàng trước camera.
3. Khi xong, quét mã kiện tiếp theo. Hệ thống tự chốt đơn trước và bắt đầu đơn mới.
4. Lặp lại cho đến khi hết kiện.
5. Cuối ca làm việc: **Đăng xuất** (xem mục 12). Trạm được tự động giải phóng.

---

## 6. Chế Độ Camera

Khi trạm có 2 camera (do Administrator cấu hình), bạn có thể chuyển chế độ:

| Chế độ | Hiển thị |
|--------|----------|
| **1 Cam** | Chỉ camera chính |
| **Dual** | Hai camera chia đôi màn hình 50/50 |
| **PIP** | Camera chính toàn màn hình, camera phụ trong ô nhỏ góc dưới bên phải |

**PIP — Hoán đổi camera:**

Trong chế độ PIP, click vào cửa sổ nhỏ (camera phụ) để **hoán đổi** camera chính và phụ. Khi có thể swap, badge **"⇄"** sẽ hiện trên ô nhỏ.

---

## 7. Grid Tổng Quan

Nút **LayoutGrid** chỉ hiện khi hệ thống có từ 2 trạm trở lên.

1. Bấm **LayoutGrid** để xem tất cả camera cùng lúc.
2. Mỗi ô hiển thị: live camera, tên trạm, và trạng thái.
3. Click vào ô bất kỳ để zoom chi tiết vào trạm đó.
4. Bấm **Maximize2** (hoặc lại **LayoutGrid**) để quay lại xem đơn lẻ.

---

## 8. Xem Lại Video

### 8.1 Lịch Sử Ghi Hình

Cột bên phải hiển thị danh sách bản ghi tại trạm đang chọn. Mỗi bản ghi gồm: mã vận đơn, chế độ ghi, trạng thái, thời gian.

Trạng thái bản ghi:

| Trạng thái | Ý nghĩa | Xem được không? |
|------------|---------|-----------------|
| 🔴 **Đang ghi hình** | Đang quay | Chưa |
| 🟡 **Đang xử lý** | Đang chuyển đổi video | Chưa |
| 🟢 **Sẵn sàng** | Hoàn tất | Click để xem |
| 🔴 **Lỗi** | Gặp sự cố | Click để xem (có thể video bị hỏng) |

### 8.2 Video Player

Click vào file video trạng thái **Sẵn sàng** để mở player.

| Thao tác | Cách thực hiện |
|----------|----------------|
| **Phát / Tạm dừng** | Nút ▶ màu xanh, hoặc click vào video, hoặc phím **Space** |
| **Tua** | Kéo thanh progress, hoặc phím **←** / **→** (mỗi lần 5 giây) |
| **Tốc độ** | Chọn 0.5x, 1x, 1.5x, 2x |
| **Âm lượng** | Biểu tượng loa + thanh trượt |
| **Chụp khung hình** | Nút xanh lá → tải file JPG về máy |
| **Tải video gốc** | Nút download → tải file video |
| **Đóng player** | Nút **X** hoặc phím **Escape** |

Thanh điều khiển tự ẩn sau 3 giây không thao tác. Di chuột vào vùng player để hiện lại.

---

## 9. Dashboard Thống Kê

Bấm **BarChart3** trên thanh header để mở Dashboard.

| Phần | Nội dung |
|------|----------|
| **Tổng Đơn Hôm Nay** | Số lượng tổng cộng + phân theo trạm |
| **Sản Xuất Theo Giờ** | Biểu đồ cột, lọc theo ngày và trạm |
| **Xu Hướng 7 Ngày** | Biểu đồ đường |
| **So Sánh Trạm** | Biểu đồ tròn |
| **Xuất CSV** | Tải dữ liệu dạng file CSV, mở được bằng Excel |

---

## 10. Chuyển Trạm

1. Bấm dropdown **Trạm: {tên}** trên thanh header.
2. Chọn trạm khác.

Hệ thống kiểm tra trạng thái trạm mới:

- Nếu trạm **trống** → chuyển thành công. Trạm cũ được tự giải phóng.
- Nếu trạm **đang dùng** → hiện thông báo: "Trạm này đang được sử dụng bởi {tên}". Bạn không thể chuyển sang.

Nếu chuyển thất bại, hệ thống tự kết nối lại trạm cũ để bạn tiếp tục làm việc.

---

## 11. Đổi Mật Khẩu

1. Bấm tên user (góc phải trên thanh header).
2. Chọn **Đổi mật khẩu**.
3. Nhập **Mật khẩu hiện tại**.
4. Nhập **Mật khẩu mới** (tối thiểu 6 ký tự).
5. Nhập lại **Xác nhận mật khẩu**.
6. Bấm **Đổi mật khẩu** hoặc nhấn **Enter**.

Thành công: hiện thông báo "Đổi mật khẩu thành công!".

---

## 12. Đăng Xuất

1. Bấm tên user (góc phải trên thanh header).
2. Chọn **Đăng xuất**.

Trạm bạn đang giữ sẽ được **tự động giải phóng**, người khác có thể sử dụng.

> Khuyến nghị: Luôn đăng xuất đúng cách khi kết thúc ca làm việc. Đừng chỉ đóng tab trình duyệt.

---

## 13. Khắc Phục Sự Cố Thường Gặp

| Vấn đề | Giải pháp |
|---------|-----------|
| Không truy cập được trang web | Kiểm tra máy chủ đang chạy chưa. Báo Administrator. |
| Camera không hiển thị | Báo Administrator kiểm tra kết nối camera. |
| "Trạm đang được sử dụng" | Chọn trạm khác, hoặc chờ người kia đăng xuất. |
| Trạng thái "Đang xử lý" lâu | Bình thường. Video lớn cần thời gian chuyển đổi, hãy đợi thêm. |
| Bị tự đăng xuất | Token hết hạn sau 8 giờ. Đăng nhập lại là xong. |
| Không thấy nút Grid | Cần 2 trạm trở lên nút **LayoutGrid** mới hiện. |
| Không thấy chế độ Dual/PIP | Trạm chỉ có 1 camera. Yêu cầu Administrator cấu hình thêm camera phụ. |
| Thanh cảnh báo ổ cứng đỏ | Báo Administrator ngay để tránh mất dữ liệu. |
| Đang đóng hàng thấy tiếng beep liên tục | Tính năng Tự động dừng (Auto-stop) sắp kích hoạt. Quét mã tiếp theo để bắt đầu video mới. |
