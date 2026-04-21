# Kế Hoạch #19: Setup Modal UI Upgrade

**Phiên bản:** v2.3.1
**Ngày lập:** 2026-04-14
**Mức ưu tiên:** MEDIUM
**Trạng thái:** COMPLETED

---

## Tổng Quan

Nâng cấp SetupModal — thêm frontend validation + UX improvements để giảm lỗi nhập liệu và tăng trải nghiệm người dùng.

---

## A. FRONTEND VALIDATION RULES

Khi user bấm "LƯU TRẠM NÀY", kiểm tra trước khi gửi API:

### A1. Tên Trạm (name)
- **Bắt buộc** — không được để trống
- **Độ dài:** 2–50 ký tự
- **Không cho phép:** chỉ toàn khoảng trắng
- **Warning (không block):** Trùng tên trạm đang có → hiện confirm "Tên này đã tồn tại, tiếp tục?"

### A2. IP Camera Chính (ip_camera_1)
- **Bắt buộc** — không được để trống
- **Format:** IPv4 hoặc IPv6 hợp lệ
  - IPv4: regex `^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$`, mỗi octet 0–255
  - IPv6: regex chuẩn hoặc dùng URL constructor để validate
- **Warning:** IP không trong range LAN phổ biến (10.x, 172.16–31.x, 192.168.x, fd00::/7, fe80::/10, ::1) → hiện cảnh báo "IP này có vẻ không thuộc mạng LAN"
- **Không cho phép:** `0.0.0.0`, `127.x.x.x` (trừ khi dev), `255.255.255.255`, `::`
- **Warning:** IP trùng với station khác → hiện cảnh báo "IP này đã được dùng ở trạm X"

### A3. IP Camera Phụ (ip_camera_2)
- **Tùy chọn** — được phép để trống
- **Nếu có nhập:** validate như IP Camera Chính (IPv4 hoặc IPv6)
- **Được phép trùng IP Camera Chính** — hỗ trợ camera 1 thiết bị nhiều mắt (VD: Imou dual-lens, Tenda CH10)
- **Chỉ hiện khi:** camera_mode là `dual_file` hoặc `pip` (2 camera vật lý)

### A4. Safety Code
- **Bắt buộc** — không được để trống
- **Độ dài:** tối thiểu 4 ký tự
- **Trim khoảng trắng** trước khi lưu

### A5. MAC Address
- **Tùy chọn** — được phép để trống
- **Nếu có nhập:** phải đúng format MAC (12 hex digits, sau khi strip `:` `-` `.`)
- **Auto-format on blur:** normalize thành `AA:BB:CC:DD:EE:FF` (đã có)
- **Không cho phép:** `00:00:00:00:00:00`, broadcast `FF:FF:FF:FF:FF:FF`
- **Warning:** MAC trùng với station khác → "MAC này đã được gán cho trạm X"

### A6. Camera Brand
- **Bắt buộc** — dropdown, luôn có giá trị (default: imou)

### A7. Camera Mode
- **Bắt buộc** — dropdown, luôn có giá trị (default: single)
- **Nếu chọn `single`** → ẩn field ip_camera_2
- **Nếu chọn `dual_file` hoặc `pip`** → hiện ip_camera_2 (optional — để trống = dùng cùng IP với camera 1, tức 1 thiết bị 2 mắt)

### A8. Keep Days
- **Bắt buộc** — dropdown, luôn có giá trị

### A9. Cloud Settings
- **Nếu chọn GDRIVE:** credentials.json phải là JSON hợp lệ (nếu có nhập)
- **Nếu chọn S3:** endpoint phải bắt đầu bằng `http://` hoặc `https://` (nếu có nhập)

---

## B. UX IMPROVEMENTS

### B1. Real-time Inline Validation
- Hiện lỗi **ngay dưới field** khi user rời input (onBlur), không đợi bấm Save
- Border đỏ + text đỏ cho field lỗi, border xanh lá cho field hợp lệ
- Nút "LƯU TRẠM NÀY" disable khi có lỗi validation

### B2. Kết nối Camera Test Button
- Thêm nút "Test kết nối" bên cạnh IP Camera 1
- Gọi `GET /api/network-info` hoặc ping IP → hiện trạng thái: ✅ Reachable / ❌ Unreachable / ⏳ Timeout
- Giúp user xác nhận IP đúng trước khi save

### B3. Auto-detect Camera Brand từ IP
- Khi user nhập IP + quét MAC thành công → có thể hint brand dựa trên MAC prefix (OUI)
- Không block, chỉ gợi ý

### B4. Conditional Field Visibility
- `ip_camera_2` chỉ hiện khi mode `dual_file` hoặc `pip` (optional — để trống = cùng IP, hỗ trợ 1 thiết bị nhiều mắt)
- Camera mode description ngắn gọn bên dưới dropdown:
  - `single`: "Ghi 1 luồng từ 1 camera"
  - `pip`: "Ghép hình-in-picture từ 2 camera (hoặc 1 camera 2 mắt)"
  - `dual_file`: "Ghi 2 file riêng từ 2 camera (hoặc 1 camera 2 mắt)"
- Cloud provider fields chỉ hiện khi chọn provider đó (đã có)

### B5. Safety Code Toggle Visibility
- Nút "👁" bên cạnh Safety Code để hiện/ẩn password
- Hiện masked mặc định (đã là `type="password"`)

### B6. Unsaved Changes Warning
- Track dirty state — nếu user thay đổi bất kỳ field nào → bấm HỦY hoặc click X → confirm "Bạn có thay đổi chưa lưu. Thoát?"
- Reset dirty flag sau khi save thành công

### B7. Section Collapsible
- "Cấu hình Trạm" luôn mở
- "Hệ thống chung" + "Telegram" — collapse/expand để giảm scroll
- Hoặc tách thành tabs: "Trạm" | "Hệ thống" | "Telegram"

### B8. Clear Field Buttons
- Nút "×" nhỏ trong mỗi input text để xóa nhanh (X button)

### B9. Responsive Improvements
- Trên mobile: modal full-screen thay vì centered box
- Fields xếp dọc, padding giảm

---

## C. IMPLEMENTATION PRIORITY

### Phase 1 — Core Validation (Must Have)
- A1–A8: Tất cả validation rules
- B1: Real-time inline validation
- B4: Conditional field visibility (ip_camera_2)
- B5: Safety Code toggle

### Phase 2 — UX Polish (Should Have)
- B2: Test kết nối camera
- B6: Unsaved changes warning
- B7: Section collapsible hoặc tabs

### Phase 3 — Nice to Have
- B3: Auto-detect brand từ MAC
- B8: Clear field buttons
- B9: Mobile responsive

---

## Files Cần Sửa

| File | Action |
|------|--------|
| `web-ui/src/SetupModal.jsx` | Rewrite — thêm validation logic, UX improvements |
| `api.py` | Thêm endpoint `GET /api/stations/check-conflict` (check IP/MAC trùng) |

## Ghi Chú

- Validation frontend chỉ là UX — backend vẫn validate (defense in depth)
- Không thay đổi DB schema hay backend logic
- Phase 1 có thể implement ngay, Phase 2/3 tùy thời gian
