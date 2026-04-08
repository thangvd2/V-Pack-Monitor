# Kế Hoạch Triển Khai Giai Đoạn 9: Hoàn Thiện & Đa Nhiệm (Maturity Phase)

Chào bạn, đây là bản thiết kế cho hạng mục Dọn code, Nâng cấp Chatbot và Hoàn thiện tài liệu mà bạn vừa yêu cầu.

## Giải đáp: Tại sao chưa thấy file `.exe`?

Trình đóng gói **Pyinstaller không có khả năng dịch chéo hệ điều hành (Cross-Compile)**. Vì file `build.py` vừa nãy được tự động kích hoạt và biên dịch trực tiếp trên chiếc Laptop **MacBook (MacOS)** của bạn, nên thành phẩm nó đẻ ra trong thư mục `dist/` sẽ là tập tin `V-Pack-Monitor.app` (Cho Mac) chứ không phải `.exe`.

Để ra được file `.exe`, bạn chỉ cần copy nguyên mục `camdonghang` này ném sang 1 máy tính **Windows** bất kỳ, rồi gõ đúng câu lệnh `python build.py` y hệt, Pyinstaller trên Windows lúc đó sẽ cho ra cái file `.exe` đuôi mà bạn thắc mắc nhé! (Hoặc có thể dựng GitHub Actions cấu hình máy chủ Windows để làm từ xa ở Bước 4).

---

## Tính năng 1: Dọn Dẹp "Nợ Kỹ Thuật" & Linter (Code Hygiene)
Dọn sạch rác, cảnh báo và chuẩn hoá (PEP8) để mã nguồn bóng loáng và dễ bảo trì.

### Các Codebase cần dọn:
- **`database.py`**: Fix lỗi cách dòng sai (blank line whitespace), quá 79 kí tự (line too long), sửa lỗi thiếu 2 blank line trước khai báo hàm.
- **`camera_config.py`**: Sửa lỗi khoảng trắng thừa (trailing whitespace), căn chỉnh độ dài mảng Config để Linter hết báo đỏ.
- **`api.py` & `cloud_sync.py` & `telegram_bot.py`**: Xoá các Import không dùng tới, gộp các Block comment gọn gàng. Tối ưu hoá tên biến.

## Tính năng 2: Nâng Cấp Chatbot Telegram 2 chiều (Lắng nghe & Trả lời)
Trước đây Bot chỉ nhận lệnh và nhắn (1 chiều). Giờ ta sẽ cấy cho Bot cái "Tai" để nghe lệnh từ Chủ kho và lập tức gửi trả về Báo cáo (2 chiều).

### Ý tưởng kỹ thuật Backend (`telegram_bot.py` & `api.py`)
- Cài đặt thư viện chuyên dụng `pyTelegramBotAPI` (hay Telebot).
- Kích hoạt trình **Background Polling** (Lắng nghe ngầm) chạy song song với `FastAPI` (trong hàm `lifespan` hoặc Thread riêng).
- Khi người dùng Chat vào Bot 1 trong các lệnh:
  - `/baocao`: Bot sẽ kết nối Database SQLite, đếm tổng số Video Packing trong ngày hôm nay, dung lượng ổ cứng hiện tại báo cáo lại.
  - `/kiemtra`: Bot báo cáo Station nào đang bật, Camera nào đang hoạt động.
- Sẽ có cơ chế **Whitelist Chat ID**: Bot chỉ nghe và trả lời những người chủ kho (Chat ID trùng với config trong settings), người lạ chat nó sẽ im lặng bảo mật!

## Tính năng 3: Xây dựng Tài Liệu & Lịch Sử Nâng Cấp (Documentation)

### `README.md`
- Xây dựng lại giao diện `README.md` thật "Pro" có chứa sơ đồ tính năng.
- Mục Hướng dẫn Cài đặt & Khởi chạy (Cách chạy Dev, cách chạy Production Build.py).
- Thông tin cảnh báo lỗi cài đặt phổ biến (Troubleshooting).

### `RELEASE_NOTES.md`
- Viết Changelog công bố ra mắt phiên bản **V-Pack Monitor v1.3.0 Premium**. Liệt kê những thay đổi từ trước tới nay. Cấu trúc chuyên trị chuẩn GitHub Changelog, dễ dàng dùng để Post status giới thiệu anh em cộng đồng hoặc báo cáo khách hàng.

---

> [!IMPORTANT]
> - Đối với tính năng Telegram, tôi sẽ cài đặt thêm thư viện `pyTelegramBotAPI` qua `pip`.
> - Telegram Long Polling là một vòng lặp vĩnh viễn (While True), tôi sẽ phải nhốt nó vào 1 `daemon Thread` trên FastAPI để không làm tê liệt Web Server. Bạn đánh giá kiến trúc xử lý Threading này ổn chứ?
> 
> Nếu bạn **Đồng ý** với kế hoạch này, hãy trả lời để tôi tiến hành bắt tay vào xử lý nhé!
