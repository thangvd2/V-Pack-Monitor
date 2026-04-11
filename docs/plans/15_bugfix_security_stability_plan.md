# Kế Hoạch Fix Bug #15: Bảo Mật & Ổn Định Hệ Thống (Security & Stability Patch)

**Phiên bản:** v2.2.1-hotfix
**Ngày lập:** 2026-04-12
**Mức ưu tiên:** CRITICAL / HIGH
**Trạng thái:** PENDING

---

## Tổng Quan

Bản vá tổng hợp 8 lỗi nghiêm trọng được phát hiện qua code review toàn bộ codebase (commit `f23cee0`). Bao gồm 3 lỗi CRITICAL (bảo mật, tương thích Windows), 4 lỗi HIGH (mất dữ liệu, rò rỉ thông tin), 1 lỗi LOW (frontend stale state).

---

## Bug #1 [CRITICAL] — Hardcoded JWT Secret Key

**File:** `auth.py:16-18`
**Vấn đề:** Fallback secret key `"vpack-monitor-secret-key-2026-change-in-production"` nằm trực tiếp trong source code. Bất kỳ ai đọc được source có thể forge JWT token → chiếm quyền Admin.
**Cách fix:**

1. Xóa fallback string cứng, thay bằng auto-generate secret ngẫu nhiên lần đầu chạy:
   - Nếu env var `VPACK_SECRET` không tồn tại → generate random 64-char hex string
   - Lưu vào `system_settings` table với key `JWT_SECRET`
   - Lần khởi động sau, đọc từ DB trước, fallback sang generate mới nếu mất
2. Cập nhật `auth.py`:
   ```python
   SECRET_KEY = os.environ.get("VPACK_SECRET") or database.get_setting("JWT_SECRET") or _generate_secret()
   ```
   Hàm `_generate_secret()` sẽ generate, lưu vào DB, và return.

**Test:**
- Xóa env var `VPACK_SECRET` → restart server → verify token vẫn hoạt động sau restart (đọc từ DB)
- Set env var → verify dùng env var

---

## Bug #2 [CRITICAL] — GET /api/stations Không Yêu Cầu Auth

**File:** `api.py:657-659`
**Vấn đề:** Endpoint `GET /api/stations` không có dependency `CurrentUser` → bất kỳ ai truy cập được toàn bộ IP camera, safety code, MAC address của tất cả trạm.
**Cách fix:**

1. Thêm `CurrentUser` dependency:
   ```python
   @app.get("/api/stations")
   def get_stations_api(current_user: CurrentUser):
       return {"data": database.get_stations()}
   ```
2. Kiểm tra frontend: `fetchStations()` trong `App.jsx` đã gửi Authorization header (qua axios defaults) → tương thích.

**Test:**
- Gọi `/api/stations` không có token → 401
- Gọi `/api/stations` có token hợp lệ → 200 + data

---

## Bug #3 [CRITICAL] — Ping Command Không Tương Thích Windows

**File:** `api.py:1389`
**Vấn đề:** `["ping", "-c", "1", "-W", "1", ip]` sử dụng cờ Linux. Trên Windows, cờ đúng là `-n` (count) và `-w` (timeout ms). Camera status luôn trả về `reachable: false` trên Windows.
**Cách fix:**

1. Thêm helper dùng `platform.system()`:
   ```python
   import platform
   
   def _ping_check(ip, timeout=1):
       import subprocess
       if platform.system() == "Windows":
           cmd = ["ping", "-n", "1", "-w", str(timeout * 1000), ip]
       else:
           cmd = ["ping", "-c", "1", "-W", str(timeout), ip]
       try:
           r = subprocess.run(cmd, capture_output=True, timeout=timeout + 2)
           return r.returncode == 0
       except Exception:
           return False
   ```
2. Thay thế tại `api.py:1388-1391`:
   ```python
   alive = _ping_check(ip)
   ```

**Test:**
- Windows: verify camera reachable = true khi camera online
- Linux/macOS: verify cùng logic hoạt động

---

## Bug #4 [HIGH] — update_url() Không Re-register MediaMTX

**File:** `api.py:194-196`
**Vấn đề:** Khi IP camera thay đổi (auto-discovery hoặc manual update), `update_url()` chỉ cập nhật biến `self.url` nhưng không gọi `_mtx_register()` → live view vẫn trỏ đến RTSP URL cũ.
**Cách fix:**

1. Cập nhật `update_url()` trong class `CameraStreamManager`:
   ```python
   def update_url(self, new_url):
       with self._lock:
           self.url = new_url
       if self.station_id:
           _mtx_remove_path(self.station_id)
           self._mtx_register()
   ```
   Giống pattern đã được dùng đúng ở `update_cam2_url()` (line 198-206).

**Test:**
- Thay đổi IP camera qua Setup → verify MediaMTX path updated → live view hoạt động

---

## Bug #5 [HIGH] — Xóa File .ts Dù Transcode Thất Bại

**File:** `recorder.py:348-378`
**Vấn đề:** Khi transcode HEVC→H.264 thất bại (exception tại line 369), code vẫn tiếp tục xóa `.ts` temp file ở lines 372-378 → mất vĩnh viễn dữ liệu video gốc.
**Cách fix:**

1. Thêm flag theo dõi transcode success:
   ```python
   transcode_ok = False
   try:
       if is_hevc:
           cmd = _build_transcode_cmd(ts_path, final_path)
       else:
           cmd = [...]
       subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
       transcode_ok = True
   except Exception:
       pass

   # Only delete .ts if transcode succeeded OR non-HEVC remux succeeded
   if transcode_ok:
       for _ in range(3):
           try:
               if os.path.exists(ts_path):
                   os.remove(ts_path)
               break
           except PermissionError:
               time.sleep(1)
   else:
       # Rename .ts to .failed for manual recovery
       if os.path.exists(ts_path):
           failed_path = final_path + ".FAILED.ts"
           try:
               os.rename(ts_path, failed_path)
               print(f"Transcode failed, kept raw TS: {failed_path}")
           except Exception:
               pass
   ```

**Test:**
- Simulate transcode failure (e.g., invalid codec) → verify `.ts` file retained as `.FAILED.ts`
- Normal transcode → verify `.ts` deleted, `.mp4` created

---

## Bug #6 [HIGH] — shutdown(wait=False) Bỏ Rơi Video Đang Xử Lý

**File:** `video_worker.py:150`
**Vấn đề:** Khi server shutdown, `executor.shutdown(wait=False)` không chờ video đang transcode hoàn tất → file corrupt, record kẹt ở status PROCESSING.
**Cách fix:**

1. Đổi sang `wait=True` với timeout hợp lý:
   ```python
   def shutdown():
       global _executor
       with _lock:
           if _executor:
               _executor.shutdown(wait=True)
               _executor = None
   ```
2. Trong `api.py` lifespan, gọi shutdown trước khi kết thúc:
   - Đã có sẵn `video_worker.shutdown()` tại line 422 → chỉ cần sửa `wait=False` → `wait=True`.
   - Thêm timeout bảo vệ: nếu quá 180 giây thì force.

**Test:**
- Đang transcode video → tắt server → restart → verify video RECOVERED hoặc READY

---

## Bug #7 [HIGH] — Password Truyền Qua URL Query Parameter

**File:** Backend `api.py:629`, Frontend `UserManagementModal.jsx:206`
**Vấn đề:** Password reset gửi plaintext password qua URL query string `?password=xxx` → bị log trong access log, browser history, proxy logs.
**Cách fix:**

1. **Backend** — Đổi sang nhận password qua request body:
   ```python
   class ResetPasswordPayload(BaseModel):
       password: str
   
   @app.put("/api/users/{user_id}/password")
   def reset_password(user_id: int, payload: ResetPasswordPayload, admin: AdminUser):
       database.update_user_password(user_id, payload.password)
       ...
   ```
2. **Frontend** — Đổi từ GET param sang request body:
   ```javascript
   // UserManagementModal.jsx:206
   await axios.put(`${API_BASE}/api/users/${passwordModalId}/password`, {
       password: newPassword
   });
   ```

**Test:**
- Admin đổi password user khác → verify password được gửi trong body (check Network tab)
- Verify old password không hoạt động, new password hoạt động

---

## Bug #8 [HIGH] — UTC/Local Timestamp Mixing

**File:** `database.py:210` (insert `datetime.now()` = local) vs `database.py:293` (`datetime('now')` = UTC)
**Vấn đề:** Record được insert bằng local time (UTC+7), nhưng cleanup query dùng UTC. Record bị xóa sớm hơn 7 giờ so với mong đợi. Ví dụ: record lúc 2h sáng VN → `datetime('now')` là 19h hôm trước → có thể bị xóa nhầm.
**Cách fix:**

1. Chuẩn hóa tất cả timestamp storage về UTC:
   - `save_record()`, `create_record()`: đổi `datetime.now()` → `datetime.now(timezone.utc)`
   - Hoặc thay bằng SQLite `CURRENT_TIMESTAMP` (mặc định UTC)
2. Đồng bộ tất cả query dùng cùng timezone:
   - `cleanup_old_records()`: nếu dùng UTC storage → giữ `datetime('now')`
   - Analytics queries: đổi từ `date('now', 'localtime')` → `date('now')` nếu storage UTC, HOẶC đổi storage sang local và dùng `localtime` đồng bộ
3. **Chiến lược được chọn:** Dùng UTC storage + `CURRENT_TIMESTAMP` cho DB, convert sang local chỉ ở frontend display.
   - `save_record()` line 210: `datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")`
   - `create_record()` line 222: tương tự
   - `cleanup_old_records()` line 293: giữ nguyên `datetime('now')` (đã là UTC)
   - Analytics queries: bỏ `'localtime'` để khớp UTC storage
   - Frontend: `new Date(record.recorded_at).toLocaleString('vi-VN')` đã tự convert UTC→local → không cần sửa

**Test:**
- Insert record lúc 3h sáng VN → verify DB lưu 20h UTC hôm trước
- Cleanup 7 ngày → verify không xóa sớm
- Dashboard analytics → verify số liệu đúng

---

## Bug #9 [LOW] — SSE Stale Closure (searchTerm)

**File:** `App.jsx:257-319`
**Vấn đề:** EventSource handler closure capture giá trị `searchTerm` tại thời điểm tạo. Khi user thay đổi search term, handler vẫn dùng giá trị cũ. Dependency array thiếu `searchTerm`.
**Cách fix:**

1. Thêm `searchTerm` vào dependency array của useEffect:
   ```javascript
   }, [activeStationId, viewMode, stations, searchTerm]);
   ```
   Lưu ý: Thay đổi searchTerm sẽ đóng/mở lại EventSource connection. Đây là trade-off chấp nhận được vì search không thay đổi liên tục.

   **HOẶC** (better approach) — Dùng ref để tránh reconnect:
   ```javascript
   const searchTermRef = useRef(searchTerm);
   useEffect(() => { searchTermRef.current = searchTerm; }, [searchTerm]);
   
   // Trong SSE handler, dùng searchTermRef.current thay vì searchTerm
   ```
   Giải pháp này giữ connection SSE ổn định, chỉ cập nhật ref value.

**Test:**
- Mở trang, search "ABC" → scan barcode → verify records list refresh với đúng searchTerm

---

## Thứ Tự Thực Hiện

| Bước | Bug | Lý do ưu tiên |
|------|------|----------------|
| 1 | #1 JWT Secret | Bảo mật — ai cũng có thể forge token |
| 2 | #2 Stations No Auth | Bảo mật — rò rỉ toàn bộ camera info |
| 3 | #7 Password in URL | Bảo mật — password bị log |
| 4 | #3 Windows Ping | Tương thích — camera status sai trên production Windows |
| 5 | #4 MediaMTX Stale URL | Chức năng — live view hỏng khi IP đổi |
| 6 | #5 TS File Deletion | Dữ liệu — mất video gốc khi transcode fail |
| 7 | #6 shutdown(wait=False) | Dữ liệu — video corrupt khi tắt server |
| 8 | #8 UTC/Local Mixing | Dữ liệu — xóa sai record, analytics sai |
| 9 | #9 SSE Stale Closure | UI — search không cập nhật |

## Testing Checklist

- [ ] Login → token hoạt động bình thường
- [ ] `/api/stations` không có token → 401
- [ ] `/api/stations` có token → 200 + data
- [ ] Windows: camera reachable = true khi online
- [ ] Thay đổi IP camera → live view tự cập nhật
- [ ] Transcode fail → `.ts` được giữ lại
- [ ] Tắt server lúc đang transcode → restart → video recover
- [ ] Admin đổi password user → gửi qua body, không phải URL
- [ ] Analytics dashboard số liệu đúng giờ VN
- [ ] Search + scan barcode → records list filter đúng

## Files Cần Sửa

| File | Bugs |
|------|------|
| `auth.py` | #1 |
| `database.py` | #1, #8 |
| `api.py` | #2, #3, #4, #7 |
| `recorder.py` | #5 |
| `video_worker.py` | #6 |
| `web-ui/src/App.jsx` | #9 |
| `web-ui/src/UserManagementModal.jsx` | #7 |
| `web-ui/src/Dashboard.jsx` | #8 (analytics query timezone) |

## Ghi Chú

- Bug #1 (JWT secret): Cần migration strategy — token cũ sẽ invalid sau khi đổi secret. Cần force logout tất cả user.
- Bug #8 (timezone): Record cũ đã insert bằng local time. Cần migration script để convert existing records sang UTC, HOẶC dùng `localtime` đồng bộ thay vì đổi sang UTC.
- Sau khi fix xong, cần `npm run build` trong `web-ui/` để build frontend.
- Không push code trừ khi được yêu cầu.
