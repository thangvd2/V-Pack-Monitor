# Kế Hoạch #17: Security Hardening — 26 Lỗ Hổng Bảo Mật

**Phiên bản:** v2.2.4
**Ngày lập:** 2026-04-12
**Ngày hoàn thành:** 2026-04-12
**Mức ưu tiên:** CRITICAL
**Trạng thái:** COMPLETED

---

## Tổng Quan

Security audit phát hiện 26 lỗ hổng (4 CRITICAL, 7 HIGH, 7 MEDIUM, 8 LOW). Plan này fix theo thứ tự ưu tiên.

---

## Phase 1: CRITICAL — Fix ngay

### VULN-01: Unauthenticated Video Recordings
**File:** `api.py:442`
**Vấn đề:** `/recordings/` mount static files không cần auth.
**Fix:**
1. Xóa `app.mount("/recordings", ...)`
2. Thêm authenticated download endpoint:
```python
@app.get("/api/records/{record_id}/download/{file_index}")
def download_record(record_id: int, file_index: int, current_user: CurrentUser):
    record = database.get_record_by_id(record_id)
    if not record:
        raise HTTPException(404)
    paths = record["video_paths"].split(",")
    if file_index >= len(paths):
        raise HTTPException(404)
    return FileResponse(paths[file_index])
```
3. Frontend: đổi video URL từ `/recordings/xxx.mp4` sang `/api/records/{id}/download/0`

### VULN-02: CORS Allow All Origins
**File:** `api.py:432-438`
**Fix:** Đổi sang cấu hình restrictive:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "http://127.0.0.1:8001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
Hoặc dynamic origin từ request header.

### VULN-03: Default Admin Password
**File:** `database.py:131-141`
**Fix:**
1. Không print password ra console
2. Thêm cột `must_change_password` vào users table
3. Lần đầu login với default password → bắt buộc đổi
4. Hoặc: generate random password, chỉ hiển thị 1 lần

### VULN-04: Safety Code Exposed to OPERATOR
**File:** `database.py:349`, `api.py:667`
**Fix:**
1. Tạo hàm `get_stations_safe()` — trả về data không có `safety_code`
2. API `/api/stations` cho OPERATOR dùng `get_stations_safe()`
3. ADMIN vẫn thấy `safety_code` (qua endpoint riêng hoặc flag)

---

## Phase 2: HIGH — Fix trong tuần

### VULN-05: Login Rate Limiting
**Fix:** Thêm `slowapi` hoặc simple in-memory rate limiter:
```python
_login_attempts = {}  # {ip: [timestamps]}
MAX_ATTEMPTS = 5
WINDOW_SECONDS = 300

@app.post("/api/auth/login")
def login(payload, request: Request):
    ip = request.client.host
    # check rate limit...
```

### VULN-06: JWT Token Revocation
**Fix:** Thêm bảng `revoked_tokens` hoặc check `password_changed_at` vs token `iat`.

### VULN-07: SSE Events Unauthenticated
**File:** `api.py:1261`
**Fix:** Thêm `current_user: CurrentUser` dependency. Frontend gửi token qua query param hoặc header (EventSource hỗ trợ header qua workaround).

**Lưu ý:** EventSource API không hỗ trợ custom headers. Workaround:
- Option A: Token qua query param `?token=xxx` (chỉ dùng cho SSE)
- Option B: Dùng `fetch` + `ReadableStream` thay `EventSource`
- Option C: Tạo short-lived SSE token qua authenticated endpoint trước

**Chọn Option A** (đơn giản nhất, token chỉ dùng cho SSE, không phải REST API).

### VULN-08: Credentials Upload Validation
**Fix:** Validate JSON structure trước khi ghi file.

### VULN-09: SQL Injection Prevention
**Fix:** Whitelist column names trong `update_station_ip`, `update_user`. Dùng parameterized queries thay f-string.

### VULN-10: Mask Sensitive Settings
**Fix:** GET `/api/settings` mask `S3_SECRET_KEY`, `TELEGRAM_BOT_TOKEN` — chỉ hiện 4 ký tự cuối. Client gửi full value khi PUT.

### VULN-11: TLS / HTTPS
**Fix:** Không thể fix trong code dễ dàng. Khuyến nghị dùng nginx reverse proxy. Note trong README.

---

## Phase 3: MEDIUM — Fix sprint này

### VULN-12: Reconnect Status Auth
Thêm `CurrentUser` dependency.

### VULN-13: Server-Side Password Validation
Thêm Pydantic validator `min_length=6`.

### VULN-14: Session Heartbeat Ownership
Check `session.user_id == current_user.id`.

### VULN-15: Encrypt Settings at Rest
AES-256 encrypt sensitive fields trong DB. Key derive từ JWT secret.

### VULN-16: Telegram Bot Token in URL
Dùng header-based auth thay URL embed.

### VULN-17: RTSP URL Logging
Sanitize URLs trước khi log.

### VULN-18: Generic Error Messages
Không trả raw exception cho client.

---

## Phase 4: LOW — Fix khi có thời gian

### VULN-19: Sequential IDs → UUIDs (không ưu tiên)
### VULN-20: IP Validation trước subprocess ping
### VULN-21: CSRF Protection (fixed khi CORS fixed)
### VULN-22: JWT Leeway giảm 30s → 5s
### VULN-23: MTX API Response Filtering
### VULN-24: Log Suppressed Exceptions at DEBUG
### VULN-25: Input Length Limits (barcode max 100 chars)
### VULN-26: Redact FFmpeg Command Lines

---

## Files Cần Sửa

| File | Phase | VULNs |
|------|-------|-------|
| `api.py` | 1-4 | 01,02,04,05,07,08,10,12,13,14,17,18,23,25,26 |
| `database.py` | 1-3 | 03,04,09,15 |
| `auth.py` | 2 | 06,22 |
| `web-ui/src/App.jsx` | 1-2 | 01,07 (SSE auth) |
| `web-ui/src/SetupModal.jsx` | 1 | 04 (không gửi safety_code cho operator) |
| `web-ui/src/VideoPlayerModal.jsx` | 1 | 01 (download URL) |
| `telegram_bot.py` | 3 | 16 |

## Testing Checklist

- [ ] `/recordings/` trả 404 (không serve static nữa)
- [ ] Download video qua API cần JWT token
- [ ] OPERATOR không thấy safety_code
- [ ] ADMIN thấy safety_code
- [ ] CORS block request từ origin khác
- [ ] Login fail 5 lần → lock 5 phút
- [ ] SSE cần token
- [ ] Settings API mask S3_SECRET_KEY
- [ ] Password mới < 6 ký tự → rejected server-side
- [ ] Default admin phải đổi password lần đầu
