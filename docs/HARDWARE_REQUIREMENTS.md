# 🖥️ V-Pack Monitor — Cấu hình Windows cho 2 Camera Dahua (PTZ + Fixed)

## Kịch bản tham khảo
- **Camera 1**: Dahua PTZ 4MP (DH-SD49425XB-HNR hoặc tương đương)
- **Camera 2**: Dahua Fixed 4MP (DH-IPC-HFW series hoặc tương đương)
- **Mỗi camera**: Dual-stream (Main + Sub) chạy đồng thời
- **Gói hàng**: ~100 đơn/ngày, trung bình 30s/video

---

## 1. Tải hệ thống — Phân tích chi tiết

### a) Quá trình ghi — FFmpeg

| Chế độ | Tiêu đề FFmpeg | CPU | Ghi chú |
|-------|-----------------------|-----|---------|
| **ĐƠN** (1 camera) | `-c:v copy -c:a copy` (stream copy) | ~2-5% | Ghi bằng 0 |
| **DUAL_FILE** (2 camera) | 2× `-c:v copy -c:a copy` | ~3-8% | Vẫn copy luồng |
| **PIP** (2 camera ghép) | `filter_complex` + encode 15fps | ~20-50% 1 nhân | **CPU cao nhất** — giải mã 2 luồng → scale → overlay → mã hóa |

### b) Hậu kỳ — MPEG-TS → MP4

| Loại luồng | Xử lý | CPU | Ghi chú |
|------------|---------|-----|---------|
| **H.264** | Remux (`-c copy`) | ~1-2% | Chỉ đổi container |
| **H.265/HEVC** | Transcode HEVC→H.264 | **30-80% 1 nhân** (CPU) / ~5-15% (GPU) | **Nút thắt CPU lớn nhất** |

### c) Hệ thống nền

| Thành phần | CPU | RAM |
|-----------|-----|-----|
| FastAPI (uvicorn) | <1% | 50-80 MB |
| MediaMTX (2 WebRTC passthrough) | <2% | 40-80 MB |
| SQLite (WAL) | <1% | 5-15 MB |
| Luồng Telegram Bot | <1% | 5-10 MB |
| Theo dõi Camera (2 luồng) | <1% | 5-10 MB |
| Kiểm tra sức khỏe Camera (60 giây) | Burst <5% | <5 MB |

### d) Mạng — Băng thông Camera

| Luồng | Camera PTZ 4MP | Camera Cố định 4MP |
|-------|-----------------|---------------------|
| Chính (ghi, H.265) | ~4 Mbps | ~4 Mbps |
| Phụ (xem trực tiếp WebRTC, H.264) | ~0.5 Mbps | ~0.5 Mbps |
| **Tổng mỗi camera** | **~4.5 Mbps** | **~4.5 Mbps** |
| **Tổng 2 camera** | | **~9 Mbps** |

> Camera Dahua chỉ có port 10/100 Mbps — nhưng 100 Mbps >> 9 Mbps cần thiết, nên không vấn đề.

### e) Dung lượng ổ đĩa

| Kịch bản | Mỗi ngày | Mỗi tháng | Mỗi 6 tháng |
|----------|-----------|-----------|-------------|
| 100 đơn × 30s, H.265 4MP | ~150 MB | ~4.5 GB | ~27 GB |
| 10 giờ ghi liên tục, H.265 4MP | ~36 GB | ~1.1 TB | ~6.5 TB |
| 24/7 Smart H.265+ | ~8 GB | ~240 GB | ~1.4 TB |

---

## 2. CẤU HÌNH TỐI THIỂU

> Chạy ổn định với H.264 camera (không transcode), chế độ ĐƠN hoặc TỆP_ĐÔI

| Thiết bị | Yêu cầu |
|-----------|-----------|
| **CPU** | Intel Celeron / i3 thế hệ 6+ (**2 nhân**) |
| **RAM** | **4 GB** DDR4 |
| **Ổ cứng** | **256 GB SSD** |
| **GPU** | Không cần thiết |
| **Mạng** | 100 Mbps LAN + Switch 5+ port |
| **Nguồn** | 300W |
| **HĐH** | Windows 10 64-bit |

**Lý do**: Khi camera output H.264, hệ thống chỉ làm stream copy (`-c:v copy`) — gần như không tiêu tốn CPU. FFmpeg chỉ chuyển đổi luồng từ RTSP sang MPEG-TS.

**💡 Mẹo**: Cấu hình camera Dahua thành H.264 thay vì H.265 trong Web UI → loại bỏ hoàn toàn transcode.

---

## 3. CẤU HÌNH ĐỀ XUẤT

> Chạy mượt mọi chế độ, bao gồm H.265 camera, PIP mode, cloud sync

| Thiết bị | Yêu cầu | Ghi chú |
|-----------|-----------|---------|
| **CPU** | Intel Core i3/i5 thế hệ 6+ (**4 nhân**) | Có Quick Sync Video (QSV) |
| **RAM** | **8 GB** DDR4 | |
| **Ổ cứng** | **512 GB SSD** (hệ thống) + **1 TB HDD** (lưu trữ) | SSD cho Windows + app, HDD cho recordings |
| **GPU** | **Intel UHD tích hợp** (QSV) | Đã có sẵn trong CPU i3/i5 — không cần mua rời |
| **Mạng** | Gigabit LAN + Switch 5+ port Gigabit | |
| **Nguồn** | 400W | |
| **HĐH** | Windows 10/11 64-bit | |

**Tại sao Intel Quick Sync quan trọng**:
- H.265 → H.264 transcode: giảm từ **40-80% CPU** → **~5-15% CPU**
- Được tự động nhận diện bởi `recorder.py` (ưu tiên QSV đầu tiên)
- Không cần mua GPU rời — có sẵn trong mọi CPU Intel từ thế hệ 6+
- PIP mode encode cũng dùng QSV → giảm CPU đáng kể

---

## 4. Bảng so sánh nhanh

| | Tối thiểu | Đề xuất | Nâng cao |
|---|-----------|-----------|---------|
| **CPU** | 2 nhân (Celeron/i3) | 4 nhân + QSV (i3/i5) | 6+ nhân + NVIDIA GPU |
| **RAM** | 4 GB | 8 GB | 16 GB |
| **Ổ cứng** | 256 GB SSD | 512 GB SSD + 1 TB HDD | 1 TB NVMe + 2 TB HDD |
| **GPU** | Không cần | Intel QSV (tích hợp) | NVIDIA GTX 1650+ (NVENC) |
| **Mạng** | 100 Mbps | Gigabit | Gigabit |
| **Trường hợp sử dụng** | H.264 only, ĐƠN/DUAL_FILE | H.265 + PIP + cloud sync | 4+ cameras, 24/7 ghi |

---

## 5. Dung lượng phần mềm cài đặt

| Thành phần | Kích thước |
|-------------|--------|
| Python venv + dependencies | ~300 MB |
| FFmpeg binaries (ffmpeg + ffprobe + ffplay) | ~591 MB |
| MediaMTX | ~50 MB |
| Giao diện người dùng Web (đã xây dựng) | ~1 MB |
| SQLite DB | <10 MB |
| **Tổng dung lượng cài đặt** | **~950 MB** |

---

## 6. Lưu ý quan trọng

1. **Cấu hình camera thành H.264** nếu máy yếu → loại bỏ hoàn toàn nhu cầu transcode, CPU load giảm 90%
2. **PIP mode là nặng nhất** — decode 2 luồng + filter_complex + encode. Nếu dùng máy cấu hình tối thiểu, tránh PIP, dùng DUAL_FILE thay thế
3. **MediaMTX gần như không tốn CPU** — chỉ proxy RTSP→WebRTC, sub-stream nhỏ (D1 704×576)
4. **Quét mạng tự động** (auto-discovery) gây CPU spike ngắn (~3-5 giây) khi quét /24 subnet — chỉ chạy khi cần tìm lại camera
5. **Cloud sync** nén ZIP tất cả video chưa đồng bộ rồi upload — tốn CPU ngắn khi nén, tốn băng thông upload tùy số lượng video
