# Plan: Auto-Discovery Camera by MAC Address

**Version:** 1.3.1
**Date:** 2026-04-08
**Author:** VDT - Vu Duc Thang

---

## Problem

Khi modem/router DHCP reset hoặc có sự cố mạng, camera IP nhận địa chỉ IP mới. Hệ thống V-Pack Monitor hiện lưu `ip_camera_1`/`ip_camera_2` cố định trong SQLite → RTSP URL chết → không thể ghi hình.

## Solution: MAC-based Auto Rediscovery

Lưu thêm MAC Address của mỗi camera. Khi kết nối RTSP thất bại, hệ thống tự động quét LAN tìm IP mới theo MAC, cập nhật DB, và tự kết nối lại.

---

## Files to Create

### 1. `network.py` (NEW) - LAN Scanner Module

**Purpose:** Quét mạng LAN tìm IP device theo MAC address.

```
Functions:
- scan_lan_for_mac(target_mac, subnet=None) -> str | None
  + Dùng ARP table (subprocess arp -a) để tìm nhanh
  + Fallback: ping sweep subnet + ARP nếu chưa thấy
  + Normalize MAC format (AA:BB:CC vs AA-BB-CC vs aabb.cc)
  + Return IP string hoặc None

- get_local_subnet() -> str
  + Detect subnet tự động từ network interface (VD: 192.168.1.0/24)

- validate_mac(mac_str) -> bool
  + Validate MAC format trước khi lưu
```

**Tech:**
- Ưu tiên `arp -a` (có sẵn trên Windows/Mac/Linux, 0 dependency)
- Fallback `ping sweep` chỉ khi ARP table chưa có entry
- KHÔNG thêm dependency mới (no scapy, no arp-scan)

---

## Files to Modify

### 2. `database.py` - Thêm cột mac_address

**Changes:**
- `init_db()`: Thêm migration `ALTER TABLE stations ADD COLUMN mac_address TEXT DEFAULT ''`
- `get_stations()`: Thêm `mac_address` vào SELECT + dict response
- `get_station()`: Thêm `mac_address` vào SELECT + dict response
- `update_station()`: Thêm `mac_address` vào UPDATE SET
- `add_station()`: Thêm `mac_address` vào INSERT
- Tạo mới `update_station_ip(station_id, field, new_ip)`: cập nhật IP đơn lẻ khi rediscover

### 3. `api.py` - Auto-Reconnect Logic

**Changes:**

#### a. `StationPayload` model
- Thêm field `mac_address: str = ""`

#### b. `get_rtsp_url()` - KHÔNG sửa (giữ nguyên logic URL)

#### c. New endpoint: `POST /api/discover/{station_id}`
```
Input: station_id
Logic:
  1. Lấy station từ DB (ip_camera_1, mac_address, safety_code, camera_brand)
  2. Nếu không có mac_address → return error "Chưa cấu hình MAC"
  3. Gọi network.scan_lan_for_mac(mac_address)
  4. Nếu tìm thấy IP mới:
     - So sánh với ip_camera_1 hiện tại
     - Nếu khác → update DB (update_station_ip)
     - Cập nhật stream_managers[station_id].update_url(new_url)
     - Return {"status": "found", "old_ip": ..., "new_ip": ...}
  5. Nếu không tìm thấy → return {"status": "not_found"}
```

#### d. `CameraStreamManager._update_frame()` - Auto-trigger rediscovery
```
Khi cv2.VideoCapture() thất bại liên tục > 5 lần:
  1. Lấy station info từ DB
  2. Nếu có mac_address → gọi network.scan_lan_for_mac()
  3. Nếu tìm thấy IP mới:
     - Update DB
     - Cập nhật self.url
     - Retry kết nối
  4. Backoff: retry sau 10s, 30s, 60s (max 60s)
```

**Implementation note:** Cần thêm station_id vào CameraStreamManager để biết station nào đang fail.

#### e. `handle_scan()` - Pre-scan check
```
Trước khi tạo recorder, kiểm tra xem station có mac_address không.
Nếu có, thử ping ip_camera_1:
  - Nếu không reachable → tự trigger discover
  - Nếu discover được IP mới → dùng IP mới
  - Nếu không discover được → dùng IP cũ (hy vọng vẫn hoạt động)
```

### 4. `recorder.py` - KHÔNG SỬA
Recorder chỉ nhận RTSP URL string và ghi bằng FFmpeg. Nó không cần biết về IP discovery. Logic reconnect nằm ở api.py (CameraStreamManager).

### 5. `SetupModal.jsx` - Thêm trường MAC Address

**Changes:**
- Thêm state `macAddress`
- Thêm input field "MAC Address" sau phần IP Camera, với:
  + Placeholder: "VD: AA:BB:CC:DD:EE:FF (in ở tem đáy Camera)"
  + Helper text: "Để trống nếu không dùng tự động tìm IP"
  + Format tự động: nhập aabbccddeeff → tự format AA:BB:CC:DD:EE:FF onBlur
- Thêm `mac_address` vào payload khi save station
- Hiển thị nút "Quét tìm IP" bên cạnh IP input (gọi `/api/discover`)

### 6. `App.jsx` - Hiển thị trạng thái reconnect

**Changes:**
- Thêm state `reconnectStatus` để hiển thị khi camera đang tìm lại IP
- Hiển thị badge "Đang tìm lại Camera..." trên camera preview khi reconnecting
- Polling `/api/status` thêm field reconnect_status

---

## Database Migration (Safe)

```sql
ALTER TABLE stations ADD COLUMN mac_address TEXT DEFAULT '';
```

- Backward compatible: DEFAULT '' nên station cũ không bị ảnh hưởng
- MAC address là optional - hệ thống vẫn hoạt động bình thường nếu không nhập

---

## Testing Checklist

- [ ] Station cũ không có mac_address vẫn hoạt động bình thường
- [ ] Station mới có mac_address → khi IP đổi, auto-discover tìm đúng IP mới
- [ ] `arp -a` hoạt động trên Windows + Mac + Linux
- [ ] SetupModal hiển thị trường MAC, format đúng
- [ ] Endpoint `/api/discover/{id}` trả đúng kết quả
- [ ] CameraStreamManager auto-reconnect khi mất kết nối
- [ ] Không thêm Python dependency mới

---

## Execution Order

1. `network.py` (NEW) - tạo module quét LAN
2. `database.py` - thêm cột mac_address + migration
3. `api.py` - thêm endpoint discover + auto-reconnect trong CameraStreamManager
4. `SetupModal.jsx` - thêm UI nhập MAC
5. `App.jsx` - hiển thị trạng thái reconnect
6. Test toàn bộ
