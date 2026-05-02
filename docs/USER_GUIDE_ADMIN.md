Copyright (c) 2024-2026 VDT - Vu Duc Thang (thangvd2)

# Hướng Dẫn Sử Dụng V-Pack Monitor v3.5.0 (Dành Cho Quản Trị Viên)

---

## Mục Lục

1. [Giới Thiệu](#1-giới-thiệu)
2. [Đăng Nhập Hệ Thống](#2-đăng-nhập-hệ-thống)
3. [Tổng Quan Giao Diện](#3-tổng-quan-giao-diện)
   - [3.1 Thanh Header](#31-thanh-header)
   - [3.2 Thanh Cảnh Báo Ổ Cứng](#32-thanh-cảnh-báo-ổ-cứng)
   - [3.3 Vùng Nội Dung Chính](#33-vùng-nội-dung-chính)
4. [Cấu Hình Trạm Đóng Hàng (SetupModal)](#4-cấu-hình-trạm-đóng-hàng-setupmodal)
   - [4.1 Cấu hình Trạm](#41-cấu-hình-trạm)
   - [4.2 Hệ thống chung](#42-hệ-thống-chung)
   - [4.3 Thông Báo Telegram](#43-thông-báo-telegram)
   - [4.4 Xoá Trạm](#44-xoá-trạm)
5. [Quan Sát Live & Ghi Hình](#5-quan-sát-live--ghi-hình)
   - [5.1 Camera Live View](#51-camera-live-view)
   - [5.2 Chế Độ Camera](#52-chế-độ-camera)
   - [5.3 Quét Mã Vạch (Barcode)](#53-quét-mã-vạch-barcode)
   - [5.4 Lịch Sử Ghi Hình](#54-lịch-sử-ghi-hình)
6. [Video Player](#6-video-player)
7. [Grid Tổng Quan Toàn Kho](#7-grid-tổng-quan-toàn-kho)
8. [Dashboard & Thống Kê](#8-dashboard--thống-kê)
9. [Sức Khỏe Hệ Thống (chỉ ADMIN)](#9-sức-khỏe-hệ-thống-chỉ-admin)
10. [Quản Lý Người Dùng](#10-quản-lý-người-dùng)
    - [10.1 Tab Người Dùng](#101-tab-người-dùng)
    - [10.2 Tab Phiên Hoạt Động](#102-tab-phiên-hoạt-động)
    - [10.3 Tab Nhật Ký Hệ Thống](#103-tab-nhật-ký-hệ-thống)
11. [Đồng Bộ Cloud](#11-đồng-bộ-cloud)
12. [Đổi Mật Khẩu & Đăng Xuất](#12-đổi-mật-khẩu--đăng-xuất)
13. [Khắc Phục Sự Cố](#13-khắc-phục-sự-cố)

---

## 1. Giới Thiệu

**V-Pack Monitor** là hệ thống ghi hình camera kết hợp quét mã vạch, thiết kế riêng cho kho hàng thương mại điện tử. Hệ thống tự động đồng bộ cảnh camera với từng mã vận đơn, giúp quản lý dễ dàng tra cứu, kiểm tra và lưu trữ bằng chứng đóng gói.

Hệ thống phân quyền hai cấp:

- **ADMIN (Quản trị viên):** Toàn quyền quản lý trạm, camera, người dùng, theo dõi sức khỏe hệ thống và đồng bộ cloud.
- **OPERATOR (Người vận hành):** Chỉ sử dụng chức năng ghi hình và tra cứu tại trạm được gán.

Tài khoản quản trị mặc định khi cài đặt lần đầu:

| Trường | Giá trị |
|---------|----------|
| Tên đăng nhập | `admin` |
| Mật khẩu | `08012011` |

> **Lưu ý quan trọng:** Bạn nên đổi mật khẩu mặc định ngay sau khi đăng nhập lần đầu tiên để bảo đảm an toàn cho hệ thống. Xem hướng dẫn đổi mật khẩu tại [Mục 12](#12-đổi-mật-khẩu--đăng-xuất).

---

## 2. Đăng Nhập Hệ Thống

1. Mở trình duyệt web (Chrome hoặc Edge được khuyến nghị).
2. Truy cập địa chỉ: `http://localhost:8001`
3. Tại màn hình đăng nhập, nhập **"Tên đăng nhập"** và **"Mật khẩu"**.
4. Nhấn nút **"Đăng Nhập"**.

Với tài khoản **ADMIN**, sau khi đăng nhập thành công, hệ thống đưa bạn thẳng vào giao diện chính mà không cần chọn trạm. (Ngược lại, OPERATOR sẽ được yêu cầu chọn trạm trước khi vào.)

**Lưu ý về phiên đăng nhập:**

- Token xác thực hết hạn sau **8 giờ**. Khi token hết hạn, hệ thống tự động đăng xuất và đưa bạn về màn hình đăng nhập.
- Nếu bị đăng xuất bất ngờ, chỉ cần đăng nhập lại bình thường.

---

## 3. Tổng Quan Giao Diện

Giao diện chính gồm ba vùng: thanh Header phía trên, thanh cảnh báo ổ cứng (khi có cảnh báo), và vùng nội dung ở giữa.

### 3.1 Thanh Header và Điều Hướng Chức Năng

Từ phiên bản v3.4.0, hệ thống sử dụng **Thanh Điều Hướng Tab (Tab Navigation)** dành riêng cho ADMIN để tổ chức không gian làm việc khoa học hơn:

**1. Tab 📹 Vận hành:**
- Quản lý toàn bộ camera trực tiếp (Live View) và lịch sử ghi hình.
- Chế độ hiển thị mặc định là dạng lưới (Grid) tất cả các trạm.
- Nhấn vào một trạm bất kỳ (Drill-down) để xem chi tiết trạm đó. Khi vào chi tiết, bạn sẽ thấy biểu tượng **Settings** (Cài đặt Camera & Hệ thống cho Trạm này).

**2. Tab 📊 Tổng quan:**
- Bao gồm các công cụ theo dõi hệ thống.
- Chứa **Dashboard thống kê** (Sản lượng, biểu đồ 7 ngày).
- Chứa **System Health** (Sức khỏe hệ thống: CPU, RAM, Ổ cứng, Camera Health).

**Các phần tử cố định trên Header:**

| Phần tử | Mô tả |
|----------|--------|
| **Logo + tiêu đề "V-Pack Monitor"** | Tên ứng dụng, luôn hiển thị bên trái |
| **Trạm:** (dropdown) | Nút chọn trạm hiển thị đối với OPERATOR. Đối với ADMIN, tính năng này được thay thế bằng Tab Navigation ở giữa màn hình |
| **"Hôm nay: X đơn / Y đơn"** | Thống kê nhanh số đơn đã xử lý trong ngày |
| **Search** ("Tìm mã vận đơn...") | Ô tìm kiếm mã vận đơn để tra cứu nhanh |
| **HardDrive** ("Đã Sử Dụng: X GB (Y file)") | Hiển thị dung lượng ổ cứng đã dùng và số file video đang lưu trữ |
| **CloudUpload** ("Đẩy Video lên Cloud") | Mở chức năng đồng bộ video lên cloud. **Chỉ dành cho ADMIN** |
| **Users** ("Quản lý người dùng") | Được chuyển vào menu mở rộng hoặc Tab Navigation trong các phiên bản mới |
| **User dropdown** (Tên + role badge) | Hiển thị tên người đăng nhập và nhãn vai trò. Nhấn vào để thấy tùy chọn **Đổi mật khẩu** và **Đăng xuất** |

### 3.2 Thanh Cảnh Báo Ổ Cứng

Thanh này xuất hiện ngay dưới Header khi ổ cứng sắp đầy:

| Màu sắc | Ý nghĩa |
|----------|----------|
| Xanh | Ổ cứng bình thường, không cảnh báo |
| Đỏ nhấp nháy + thông báo **"Cảnh Báo: Ổ Cứng Sắp Đầy!"** | Ổ cứng đã sử dụng trên 90% dung lượng. Cần xử lý ngay |

Khi thấy cảnh báo đỏ, hãy xoá video cũ hoặc giảm số ngày lưu trữ (xem [Mục 4.2](#42-hệ-thống-chung) và [Mục 13](#13-khắc-phục-sự-cố)).

### 3.3 Vùng Nội Dung Chính

Vùng nội dung chính hiển thị một trong các chế độ sau:

1. **Admin Tab Navigation (Chế độ mặc định của ADMIN)**:
   - **Tab Vận hành**: Lưới (Grid) của tất cả camera các trạm với trạng thái live view và ghi hình. Nhấn vào một trạm để vào giao diện chi tiết (Drill-down).
   - **Tab Tổng quan**: Dashboard thống kê kết hợp với thông tin Sức khỏe hệ thống.
2. **Camera Live + Lịch sử ghi hình** (Khi vào chi tiết một trạm hoặc với OPERATOR). Hiển thị camera trực tiếp ở bên trái và danh sách lịch sử ghi hình ở cột bên phải.
3. **Dashboard thống kê**. Xem chi tiết tại [Mục 8](#8-dashboard--thống-kê).
4. **System Health (Sức khỏe hệ thống)**. Xem chi tiết tại [Mục 9](#9-sức-khỏe-hệ-thống-chỉ-admin).
5. **Grid Tổng quan toàn kho**. (Tích hợp trong Tab Vận hành của ADMIN). Xem chi tiết tại [Mục 7](#7-grid-tổng-quan-toàn-kho).

---

## 4. Cấu Hình Trạm Đóng Hàng (SetupModal)

Cửa sổ SetupModal cho phép bạn tạo mới và chỉnh sửa cấu hình từng trạm đóng hàng. Có hai cách mở:

- Nhấn nút **Settings** (biểu tượng cái mo lê) trên thanh Header để chỉnh sửa cấu hình trạm hiện tại.
- Nhấn nút **[+]** trên thanh Header để thêm trạm mới.

### 4.1 Cấu hình Trạm

| Trường | Mô tả |
|--------|--------|
| **Tên Trạm Đóng Hàng** | Tên hiển thị của trạm trên giao diện. Ví dụ: "Bàn Chốt Đơn 1", "Khu Vực Đóng Gói A" |
| **IP Camera Chính** | Địa chỉ IP của camera chính. Ví dụ: `192.168.5.18` |
| **IP Camera Phụ** | Địa chỉ IP của camera thứ hai. Bỏ trống nếu trạm chỉ dùng một camera |
| **Hãng Camera** | Chọn hãng camera từ danh sách: **Imou/Dahua** (mặc định), **Tenda**, **EZVIZ**, **TP-Link Tapo** |
| **Mật khẩu RTSP / Safety Code** | Mã an toàn in trên vỏ camera. Dùng để xác thực kết nối RTSP |
| **MAC Address** | Địa chỉ MAC của camera, định dạng `AA:BB:CC:DD:EE:FF`. Có thể nhập tay hoặc dùng nút **"Quét IP"** để tự động tìm camera trong mạng cục bộ khi bạn thay đổi địa chỉ IP |
| **Chất Lượng Ghi Hình** | Lựa chọn độ phân giải video lưu trữ (chỉ khả dụng ở chế độ ghi SINGLE): **1080p (Main stream - Sắc nét)** hoặc **480p (Sub stream - Tiết kiệm)** |
| **Chế độ ghi Video** | Chọn cách ghi video cho trạm. Các chế độ có sẵn: |

Chi tiết các chế độ ghi video:

| Chế độ | Mô tả |
|--------|--------|
| **SINGLE** | Ghi từ một camera chính duy nhất (hỗ trợ chọn Chất Lượng Ghi Hình) |
| **PIP** | Camera chính toàn màn hình, camera phụ chèn nhỏ ở góc (Picture-in-Picture) |
| **DUAL_FILE** | Ghi hai file video riêng biệt, mỗi camera một file |

### 4.2 Hệ thống chung

Trong phần này, bạn cấu hình các thiết lập toàn cục áp dụng cho trạm:

**Quản lý video cũ:**

| Trường | Mô tả |
|--------|--------|
| **Tự động xoá Video cũ hơn** | Chọn số ngày giữ video: **3**, **7**, **15**, hoặc **30** ngày. Video cũ hơn thời gian này sẽ bị hệ thống tự động xoá |

**Dịch vụ Lưu Trữ Đám Mây:**

| Dịch vụ | Thông tin cần cấu hình |
|----------|------------------------|
| **NONE** | Không đồng bộ cloud. Video chỉ lưu trên ổ cứng cục bộ |
| **Google Drive** | Cần cung cấp **Folder ID** (ID thư mục Google Drive) và file **credentials.json** (tải từ Google Cloud Console) |
| **S3/R2** | Cần cung cấp: **Endpoint URL**, **Access Key**, **Secret Key**, **Bucket Name**. Tương thích với Amazon S3, Cloudflare R2, và MinIO |

### 4.3 Thông Báo Telegram

Hệ thống hỗ trợ gửi thông báo qua Telegram Bot khi có sự kiện quan trọng.

| Trường | Mô tả |
|--------|--------|
| **Bot Token** | Mã token của bot Telegram |
| **Chat ID** | ID cuộc trò chuyện để bot gửi tin nhắn |

**Cách lấy Bot Token:**

1. Mở Telegram, tìm và nhắn tin với **@BotFather**.
2. Gửi lệnh `/newbot` và làm theo hướng dẫn để tạo bot mới.
3. BotFather sẽ trả về **Bot Token** (có dạng `123456789:ABCdefGHIjklMNO...`).
4. Copy và dán vào trường **Bot Token**.

**Cách lấy Chat ID:**

1. Mở Telegram, tìm và nhắn tin với **@userinfobot**.
2. Bot sẽ trả về thông tin tài khoản của bạn, bao gồm **Id** (một dãy số).
3. Copy dãy số đó và dán vào trường **Chat ID**.

### 4.4 Xoá Trạm

Nếu cần gỡ bỏ một trạm:

1. Mở SetupModal của trạm cần xoá.
2. Nhấn nút thùng rác (màu đỏ) ở góc phải trên cùng cửa sổ.
3. Xác nhận việc xoá trong hộp thoại cảnh báo.

> **Lưu ý:** Khi xoá trạm, cấu hình trạm bị gỡ bỏ nhưng các file video đã ghi vẫn được giữ lại trên ổ cứng. Trạm đã xoá không thể khôi phục, bạn cần tạo lại từ đầu nếu muốn dùng lại.

---

## 5. Quan Sát Live & Ghi Hình

### 5.1 Camera Live View

Vùng hiển thị camera trực tiếp nằm ở bên trái giao diện chính. Hệ thống sử dụng luồng **WebRTC** qua **MediaMTX**, mang lại độ trễ gần như real-time.

Các trạng thái hiển thị trên camera:

| Badge | Ý nghĩa |
|-------|----------|
| 🟢 **"Sẵn sàng"** | Camera đang hoạt động bình thường, chờ quét mã |
| 🔴 nhấp nháy **"Đang đóng hàng: [MÃ VẠCH]"** | Camera đang ghi hình, mã vạch đang xử lý hiển thị kế bên |
| ⚠️ **"Tự động dừng sau: X giây"** | Badge đếm ngược khi thời gian ghi hình gần đạt mốc Auto-stop (10 phút) |
| 📡 **"MediaMTX chưa khởi động"** | Dịch vụ MediaMTX chưa chạy. Camera không thể truyền luồng video. Cần kiểm tra và khởi động MediaMTX ở port 8889 |

**Tính Năng Tự Động Dừng (Auto-stop Timer):**
- Hệ thống tự động dừng và lưu video nếu một lần ghi hình kéo dài quá **10 phút** mà không quét mã mới.
- Ở **phút thứ 9**, hệ thống sẽ phát ra tiếng **"Beep"** cảnh báo liên tục và hiển thị badge đếm ngược trên màn hình để nhắc nhở người dùng.
- Tính năng này giúp tiết kiệm dung lượng ổ cứng trong trường hợp nhân viên quên quét mã để kết thúc kiện hàng.

### 5.2 Chế Độ Camera

Khi trạm được cấu hình hai camera (có IP Camera Phụ), bạn có thể chọn chế độ hiển thị:

| Chế độ | Mô tả |
|--------|--------|
| **1 Cam** | Hiển thị chỉ camera chính |
| **Dual** | Hai camera hiển thị song song, mỗi bên chiếm 50% màn hình |
| **PIP** | Camera chính chiếm toàn bộ màn hình. Camera phụ hiển thị nhỏ ở góc dưới bên phải |

**Thao tác với chế độ PIP:**

- Nhấn vào cửa sổ PIP nhỏ (camera phụ) để hoán đổi: camera phụ thành chính, camera chính thành phụ.
- Badge **"⇄"** xuất hiện để chỉ thị việc swap đã diễn ra.

### 5.3 Quét Mã Vạch (Barcode)

Hệ thống hỗ trợ hai cách nhập mã vạch:

**Súng quét vật lý (Barcode Scanner):**

- Cắm súng quét vào máy tính qua cổng USB.
- Súng quét tự động gửi keystroke, hệ thống nhận diện ngay không cần cấu hình thêm.
- Hướng súng về mã vạch trên vận đơn, bấm quét.

**Công cụ giả lập (trên giao diện):**

- Nhập mã vận đơn vào ô văn bản.
- Nhấn **"Bắt Đầu Ghi"** hoặc **"STOP (Chốt Đơn)"**.

**Luồng hoạt động ghi hình:**

1. Quét mã vạch vận đơn đầu tiên. Hệ thống tự động **bắt đầu ghi** video.
2. Tiếp tục quét mã vạch vận đơn tiếp theo. Hệ thống tự động chuyển sang ghi cho mã mới.
3. Quét mã **"STOP"** hoặc **"EXIT"** để **dừng ghi hình** và lưu file video.
4. Hoặc nhấn nút **"STOP (Chốt Đơn)"** trên giao diện để dừng.

Mỗi mã vận đơn sẽ tương ứng với một đoạn video riêng, giúp tra cứu dễ dàng sau này.

### 5.4 Lịch Sử Ghi Hình

Cột bên phải giao diện chính hiển thị danh sách các bản ghi của trạm hiện tại.

**Thông tin mỗi bản ghi:**

- Mã vận đơn
- Chế độ ghi (SINGLE, PIP, DUAL...)
- Trạng thái xử lý
- Thời gian ghi

**Các trạng thái bản ghi:**

| Trạng thái | Màu sắc | Ý nghĩa |
|-------------|----------|----------|
| "Đang ghi hình" | Đỏ | Camera đang quay video |
| "Đang xử lý" | Vàng | Video đã quay xong, đang convert hoặc ghép file |
| "Sẵn sàng" | Bình thường | Video đã xử lý xong, sẵn sàng phát |
| "Lỗi" | Đỏ | Xảy ra lỗi trong quá trình ghi hoặc xử lý |
| "Đã xoá" | Xám | Bản ghi đã bị xoá |

**Thao tác:**

- Nhấn vào file video để mở **Video Player** (xem [Mục 6](#6-video-player)).
- Nhấn nút thùng rác để xoá bản ghi. **Chỉ ADMIN mới có quyền xoá.**

---

## 6. Video Player

Nhấn vào bất kỳ file video nào trong lịch sử ghi hình, cửa sổ Video Player sẽ mở ra.

**Các điều khiển phát video:**

| Điều khiển | Mô tả |
|-------------|--------|
| **Play/Pause** | Phát hoặc tạm dừng video |
| **Tua ← / →** | Lùi hoặc tiến 5 giây |
| **Tốc độ** | Chọn 0.5x, 1x, 1.5x, hoặc 2x |
| **Âm lượng** | Điều chỉnh loa |

**Chức năng phụ:**

| Nút | Mô tả |
|-----|--------|
| **Snapshot** | Chụp khung hình hiện tại và tải về dạng file JPG |
| **Download** | Tải file video gốc về máy |

**Phím tắt:**

| Phím | Chức năng |
|------|-----------|
| `Space` | Play / Pause |
| `←` | Tua lùi 5 giây |
| `→` | Tua tới 5 giây |
| `Escape` | Đóng player |

Thanh điều khiển tự động ẩn sau 3 giây khi video đang phát, di chuột vào vùng player để hiện lại.

---

## 7. Grid Tổng Quan Toàn Kho

Chế độ Grid chỉ hiển thị khi hệ thống có **từ 2 trạm trở lên**.

1. Nhấn nút **LayoutGrid** trên thanh Header.
2. Màn hình hiển thị tất cả camera theo dạng lưới responsive, tự động chia đều không gian.

**Mỗi ô trong lưới hiển thị:**

- Luồng camera live
- Tên trạm
- Trạng thái ghi hình hiện tại
- Badge **"2 CAM"** nếu trạm đó có cấu hình 2 camera

Nhấn vào ô bất kỳ để zoom vào trạm đó, chuyển sang chế độ xem chi tiết.

---

## 8. Dashboard & Thống Kê

Nhấn nút **BarChart3** trên thanh Header để mở Dashboard thống kê.

**Các phần trong Dashboard:**

| Phần | Mô tả |
|------|--------|
| **Tổng Đơn Hôm Nay** | Hiển thị tổng số lượng đơn đã xử lý trong ngày, kèm phân bổ theo từng trạm |
| **Sản Xuất Theo Giờ** | Biểu đồ cột thể hiện số đơn theo từng khung giờ. Có lọc theo trạm và chọn ngày cụ thể |
| **Xu Hướng 7 Ngày** | Biểu đồ đường thể hiện xu hướng sản lượng trong 7 ngày gần nhất |
| **So Sánh Trạm** | Biểu đồ tròn so sánh sản lượng giữa các trạm |
| **Xuất CSV** | Tải dữ liệu thống kê dưới dạng file CSV, lọc theo ngày và trạm đã chọn |

Sử dụng các bộ lọc ở đầu Dashboard để thu hẹp phạm vi dữ liệu theo nhu cầu.

---

## 9. Sức Khỏe Hệ Thống (chỉ ADMIN)

Nhấn nút **Activity** trên thanh Header để mở giao diện **System Health**. Dữ liệu tự động refresh mỗi 5 giây.

### 9.1 CPU / RAM / Ổ Đĩa

Ba chỉ số tài nguyên chính được hiển thị bằng thanh progress kèm phần trăm:

| Chỉ số | Warning | Critical |
|--------|---------|----------|
| **CPU** | ≥ 80% | ≥ 95% |
| **RAM** | ≥ 85% | ≥ 95% |
| **Ổ Đĩa** | ≥ 80% | ≥ 95% |

Mỗi chỉ số có nhãn trạng thái tương ứng: **OK** (bình thường), **Warning** (cảnh báo), hoặc **Critical** (nguy hiểm).

Khi thấy trạng thái Warning hoặc Critical, kiểm tra tiến trình FFmpeg (bảng bên dưới) và cân nhắc đóng bớt ứng dụng hoặc mở rộng tài nguyên.

### 9.2 Thông Tin Máy Chủ

| Trường | Mô tả |
|--------|--------|
| **Uptime** | Thời gian server đã chạy liên tục |
| **Hostname** | Tên máy chủ |
| **IP** | Địa chỉ IP của máy chủ |

### 9.3 Tiến Trình FFmpeg

Bảng liệt kê tất cả tiến trình FFmpeg đang chạy:

| Cột | Mô tả |
|-----|--------|
| **PID** | Mã tiến trình |
| **Lệnh** | Lệnh FFmpeg đang thực thi |
| **CPU%** | Phần trăm CPU tiến trình đang dùng |
| **RAM%** | Phần trăm RAM tiến trình đang dùng |

Dùng thông tin này để xác định tiến trình nào đang ngốn nhiều tài nguyên.

### 9.4 Trạng Thái Camera (Camera Health Monitoring)

Hệ thống liên tục giám sát kết nối tới từng camera mỗi 60 giây và hiển thị bảng trạng thái:

| Trạng thái | Biểu tượng | Ý nghĩa |
|-------------|------------|----------|
| Kết nối | 🟢 | Camera trực tuyến và phản hồi bình thường |
| Mất kết nối | 🔴 | Camera không phản hồi. Khung hình camera trên Dashboard sẽ **nhấp nháy viền đỏ**. Nếu mất kết nối quá **5 phút**, hệ thống sẽ tự động gửi cảnh báo qua Telegram |

---

## 10. Quản Lý Người Dùng

Nhấn nút **Users** trên thanh Header để mở **UserManagementModal**. Giao diện quản lý người dùng gồm 3 tab.

### 10.1 Tab Người Dùng

**Thêm người dùng mới:**

1. Nhấn nút **Thêm người dùng**.
2. Điền các thông tin:
   - **Username** (tên đăng nhập)
   - **Password** (mật khẩu, tối thiểu 6 ký tự)
   - **Họ tên** (tên hiển thị)
   - **Vai trò**: chọn **ADMIN** hoặc **OPERATOR**
3. Nhấn **Lưu** để tạo tài khoản.

**Bảng danh sách người dùng:**

Hiển thị tất cả tài khoản với các cột: Username, Họ tên, Vai trò (nhãn amber cho ADMIN, nhãn blue cho OPERATOR), và Trạng thái.

**Thao tác trên từng người dùng:**

| Nút | Chức năng |
|-----|-----------|
| **Sửa** | Chỉnh sửa thông tin người dùng |
| **Đổi mật khẩu** | Đặt mật khẩu mới cho người dùng đó |
| **Khoá / Mở khoá** | Vô hiệu hoá hoặc kích hoạt lại tài khoản |
| **Xoá** | Xoá tài khoản khỏi hệ thống. Không thể xoá chính tài khoản đang đăng nhập |

### 10.2 Tab Phiên Hoạt Động

Tab này hiển thị tất cả phiên làm việc (session) đang active trên hệ thống.

**Thông tin hiển thị:**

| Cột | Mô tả |
|-----|--------|
| **Người dùng** | Tên người đang online |
| **Trạm** | Trạm họ đang làm việc |
| **Bắt đầu** | Thời điểm đăng nhập vào trạm |
| **Hoạt động cuối** | Thời điểm thao tác gần nhất |

**Kết thúc phiên:**

Nhấn nút **"Kết thúc"** ở cuối mỗi dòng để buộc người dùng đó đăng xuất khỏi trạm. Chức năng này hữu ích khi cần giải phóng trạm cho người khác, hoặc khi phát hiện session bất thường.

### 10.3 Tab Nhật Ký Hệ Thống

Tab này ghi lại mọi hoạt động trên hệ thống, phục vụ kiểm tra và truy vết.

**Bộ lọc:**

- Lọc theo **người dùng**
- Lọc theo **hành động**

**16 loại hành động được ghi nhận:**

| Mã hành động | Mô tả |
|---------------|--------|
| `LOGIN` | Đăng nhập |
| `LOGOUT` | Đăng xuất |
| `START_RECORD` | Bắt đầu ghi hình |
| `STOP_RECORD` | Dừng ghi hình |
| `CREATE_USER` | Tạo người dùng mới |
| `UPDATE_USER` | Cập nhật thông tin người dùng |
| `DELETE_USER` | Xoá người dùng |
| `CHANGE_PASSWORD` | Đổi mật khẩu |
| `LOCK_USER` | Khoá tài khoản |
| `UNLOCK_USER` | Mở khoá tài khoản |
| `FORCE_LOGOUT` | Buộc đăng xuất |
| `SETTINGS_UPDATE` | Cập nhật cài đặt |
| `STATION_CREATE` | Tạo trạm mới |
| `STATION_UPDATE` | Cập nhật cấu hình trạm |
| `STATION_DELETE` | Xoá trạm |

**Phân trang:**

Nhấn **"Tải thêm"** để tải thêm 200 bản ghi mỗi lần. Dữ liệu nhật ký tự động được dọn dẹp sau **90 ngày**.

---

## 11. Đồng Bộ Cloud

Nhấn nút **CloudUpload** ("Đẩy Video lên Cloud") trên thanh Header để mở giao diện đồng bộ. **Chỉ ADMIN mới thấy nút này.**

**Các dịch vụ hỗ trợ:**

| Dịch vụ | Yêu cầu cấu hình |
|----------|-------------------|
| **Google Drive** | Cần file `credentials.json` (tải từ Google Cloud Console). Cấu hình trong SetupModal, phần Hệ thống chung |
| **S3 / MinIO** | Cần Endpoint URL, Access Key, Secret Key, Bucket Name. Cấu hình trong SetupModal, phần Hệ thống chung |

**Thiết lập đồng bộ:**

1. Mở **SetupModal** (nhấn **Settings**).
2. Cuộn xuống phần **Hệ thống chung**.
3. Chọn dịch vụ lưu trữ đám mây và điền thông tin cấu hình tương ứng.
4. **Lập lịch đồng bộ tự động:** Bạn có thể bật tính năng "Tự động đồng bộ hàng ngày" và chọn giờ chạy (mặc định là 02:00 sáng). Hệ thống sẽ tự động đẩy video lên cloud vào giờ đã hẹn mà không ảnh hưởng tới giờ làm việc.
5. Lưu cấu hình.
6. Quay lại giao diện chính, nếu muốn chạy ngay lập tức, nhấn **CloudUpload** để bắt đầu đẩy video lên cloud.

---

## 12. Đổi Mật Khẩu & Đăng Xuất

**Đổi mật khẩu:**

1. Nhấn vào tên người dùng trên thanh Header (góc phải).
2. Chọn **"Đổi mật khẩu"**.
3. Nhập **mật khẩu cũ**.
4. Nhập **mật khẩu mới** (tối thiểu 6 ký tự).
5. Nhập lại mật khẩu mới để **xác nhận**.
6. Nhấn **Lưu** để hoàn tất.

**Đăng xuất:**

1. Nhấn vào tên người dùng trên thanh Header.
2. Chọn **"Đăng xuất"**.
3. Hệ thống đưa bạn về màn hình đăng nhập.

---

## 13. Khắc Phục Sự Cố

Bảng dưới đây tổng hợp các vấn đề thường gặp và cách xử lý:

| Vấn đề | Giải pháp |
|---------|-----------|
| **Không truy cập được web** | Kiểm tra server đang chạy chưa. Chạy `start.sh` (Linux/Mac) hoặc `start_windows.bat` (Windows) để khởi động lại |
| **Camera không hiển thị** | Kiểm tra IP camera có đúng không, port 554 có mở không, Safety Code đã nhập đúng chưa. Thử nhấn nút **"Quét IP"** trong SetupModal để tìm camera |
| **MediaMTX chưa khởi động** | Kiểm tra dịch vụ mediamtx đang chạy ở port 8889 chưa. Khởi động lại nếu cần |
| **Camera có viền đỏ nhấp nháy** | Tính năng Camera Health phát hiện camera đang offline. Kiểm tra lại nguồn điện hoặc dây mạng của camera đó |
| **Đang quét mã thì thấy "Tự động dừng sau..."** | Tính năng Auto-stop timer cảnh báo một lần quét đã kéo dài quá giới hạn. Nếu đóng kiện lâu, bạn cần quét kiện tiếp theo trước khi hết giờ |
| **Video đồng bộ bị kẹt** | Kiểm tra kết nối mạng hoặc dung lượng khả dụng trên Google Drive / S3. Thử chạy lại tính năng đồng bộ |
| **Ổ cứng sắp đầy** | Xoá video cũ trong lịch sử ghi hình, giảm giá trị **Tự động xoá Video cũ hơn** trong SetupModal, hoặc mở rộng dung lượng ổ cứng vật lý |
| **Token hết hạn** | Hệ thống tự đăng xuất sau 8 giờ. Đăng nhập lại bình thường |
| **FFmpeg không ghi** | Kiểm tra FFmpeg có trong thư mục `bin/ffmpeg/bin/` chưa. Kiểm tra ổ cứng còn trống trên 500MB không. Xem thêm tiến trình FFmpeg trong System Health |

Nếu các giải pháp trên không giải quyết được vấn đề, hãy kiểm tra log server để biết thêm chi tiết lỗi, hoặc liên hệ bộ phận kỹ thuật hỗ trợ.
