# Kế Hoạch #18: Auto-Update System

**Status**: DONE — Implemented in v3.x series.

**Phiên bản:** v2.3.0
**Ngày lập:** 2026-04-12
**Mức ưu tiên:** HIGH
**Trạng thái:** COMPLETED

---

## Tổng Quan

Thêm hệ thống tự động cập nhật. Admin bấm 1 nút → server tự update + restart. Hỗ trợ 2 mode: Dev (`git pull`) và Production (download GitHub Release ZIP).

## Kiến Trúc

### Version Tracking
- Version hiện tại lưu trong file `VERSION` (VD: `v2.2.4`)
- Backend đọc file này để biết version hiện tại
- Mỗi release trên GitHub tạo tag + upload source ZIP

### 2 Update Modes

#### Dev Mode (phát hiện bằng `.git/` folder tồn tại)
```
Startup → check .git/ exists → YES = Dev Mode
Admin bấm Update → git stash → git pull origin master → npm run build → restart
```

#### Production Mode (không có `.git/`)
```
Startup → check .git/ exists → NO = Production Mode
Admin bấm Update:
  1. GET api.github.com/repos/thangvd2/V-Pack-Monitor/releases/latest
  2. So sánh tag_name vs VERSION file
  3. Download ZIP từ assets[0].browser_download_url
  4. Backup DB: copy packing_records.db → packing_records.db.bak
  5. Giải nén ZIP vào thư mục tạm
  6. Copy đè (bỏ qua: recordings/, venv/, bin/ffmpeg/, bin/mediamtx/mediamtx.exe, *.db, *.env)
  7. pip install -r requirements.txt (nếu có thay đổi)
  8. npm run build (web-ui)
  9. Restart server
```

## Backend API

### `GET /api/system/update-check`
```python
@app.get("/api/system/update-check")
def check_update(admin: AdminUser):
    current = read_version_file()  # "v2.2.4"
    mode = "dev" if os.path.exists(".git") else "production"
    
    if mode == "dev":
        # git fetch origin, so sánh HEAD vs origin/master
        latest = git_get_latest_tag()
    else:
        # GitHub API
        latest = github_get_latest_release_tag()
    
    return {
        "current_version": current,
        "latest_version": latest,
        "update_available": latest != current,
        "mode": mode
    }
```

### `POST /api/system/update`
```python
@app.post("/api/system/update")
def perform_update(admin: AdminUser):
    mode = "dev" if os.path.exists(".git") else "production"
    
    if mode == "dev":
        return _update_dev()
    else:
        return _update_production()

def _update_dev():
    # 1. git stash
    # 2. git pull origin master
    # 3. npm run build (web-ui)
    # 4. Schedule restart sau 2 giây
    return {"status": "success", "message": "Đang cập nhật..."}

def _update_production():
    # 1. Backup DB
    # 2. Download ZIP
    # 3. Giải nén, copy đè (exclude list)
    # 4. pip install -r requirements.txt
    # 5. npm run build (web-ui)
    # 6. Schedule restart sau 2 giây
    return {"status": "success", "message": "Đang cập nhật..."}
```

### Restart Mechanism
```python
def _do_graceful_restart():
    # Chạy trong background thread (không phải request handler)
    time.sleep(1.5)  # Đợi SSE events được deliver
    
    # Graceful shutdown recorder + video worker
    for rec in active_recorders.values():
        rec.stop_recording()
    video_worker.shutdown()
    
    # Thông báo SSE "restarting"
    notify_sse("update_progress", {"stage": "restarting", ...})
    time.sleep(1.5)  # Đợi SSE delivery
    
    # Tạo restart script (tự xoá sau khi chạy)
    # Windows: _update_restart.bat → timeout 3s → start_windows.bat → del self
    # Linux: _update_restart.sh → sleep 3 → start.sh → rm self
    
    os._exit(0)  # Hard exit trong finally block
```

### Concurrent Update Protection
```python
_update_lock = threading.Lock()
_is_updating = False

@app.post("/api/system/update")
def perform_update(admin: AdminUser):
    # Double guard: lock + flag
    if not _update_lock.acquire(blocking=False):
        return error("Cập nhật đang chạy...")
    if _is_updating:
        return error("Cập nhật đang chạy...")
    
    result = _update_dev() or _update_production()
    
    # Return HTTP response TRƯỚC khi restart
    if result.status == "restarting":
        threading.Thread(target=_do_graceful_restart).start()
    return result
```

### Branch Detection
```python
def _get_git_branch():
    # Thử git rev-parse --abbrev-ref HEAD
    # Fallback: git symbolic-ref refs/remotes/origin/HEAD
    # Fallback: "master"
```

## Frontend UI

### Header Version Badge
- Luôn hiển thị version hiện tại: `[v2.2.4]`
- Check update khi startup (ADMIN only)
- Nếu có bản mới: badge vàng `[v2.2.5 ↻]`
- Click → modal xác nhận với changelog

### Update Modal
```
┌─────────────────────────────────┐
│  🔄 Cập Nhật Hệ Thống           │
│                                  │
│  Phiên bản hiện tại: v2.2.4    │
│  Phiên bản mới: v2.2.5          │
│  Mode: Production               │
│                                  │
│  ⚠️ Hệ thống sẽ restart sau khi │
│  cập nhật. Video đang ghi sẽ    │
│  được lưu tự động.              │
│                                  │
│  [Hủy]  [Cập Nhật Ngay]        │
└─────────────────────────────────┘
```

### Progress States
1. "Đang kiểm tra bản cập nhật..."
2. "Đang tải bản cập nhật..." (production only)
3. "Đang giải nén..." (production only)
4. "Đang cài đặt dependencies..."
5. "Đang build frontend..."
6. "Đang khởi động lại..."

Sử dụng SSE để push progress realtime (đã có sẵn SSE infrastructure).

## Exclude List (Production Mode)

Files/folders KHÔNG bị ghi đè khi update:
- `recordings/` — video recordings + DB
- `venv/` — Python virtual environment
- `bin/ffmpeg/` — FFmpeg binaries
- `bin/mediamtx/mediamtx.exe` — MediaMTX binary
- `bin/mediamtx/mediamtx.yml` — MediaMTX config (user có thể đã customize)
- `*.db` — SQLite databases
- `*.db.bak` — DB backups
- `*.env` — Environment variables
- `credentials.json` — Google service account
- `VERSION` — Sẽ được cập nhật riêng từ ZIP
- `install_log.txt` — Install logs

## VERSION File

Tạo file `VERSION` ở root:
```
v2.2.4
```

Được đọc bởi backend, được update khi pull/extract.
Được commit vào repo — mỗi release update file này.

## GitHub Release Workflow

Mỗi lần release bản mới:
1. Update file `VERSION` → commit → push
2. Tạo tag: `git tag v2.2.5` → `git push origin v2.2.5`
3. Tạo GitHub Release:
   - Tag: v2.2.5
   - Title: v2.2.5
   - Body: Changelog (copy từ RELEASE_NOTES.md)
   - Assets: Source ZIP (auto-generated by GitHub)

Note: GitHub tự tạo source ZIP cho mỗi release. Không cần upload thủ công.
URL format: `https://github.com/thangvd2/V-Pack-Monitor/archive/refs/tags/v2.2.5.zip`

## Flow Chi Tiết — Production Update

```python
def _update_production():
    import requests, zipfile, tempfile, shutil
    
    # 1. Get latest release info
    resp = requests.get(
        "https://api.github.com/repos/thangvd2/V-Pack-Monitor/releases/latest",
        timeout=10
    )
    release = resp.json()
    tag = release["tag_name"]
    
    # 2. Download ZIP
    zip_url = f"https://github.com/thangvd2/V-Pack-Monitor/archive/refs/tags/{tag}.zip"
    zip_resp = requests.get(zip_url, timeout=120, stream=True)
    
    # 3. Save to temp
    tmp_dir = tempfile.mkdtemp()
    zip_path = os.path.join(tmp_dir, f"{tag}.zip")
    with open(zip_path, "wb") as f:
        for chunk in zip_resp.iter_content(8192):
            f.write(chunk)
    
    # 4. Extract
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(tmp_dir)
    
    # GitHub ZIP extracts to: V-Pack-Monitor-v2.2.5/
    src_dir = os.path.join(tmp_dir, f"V-Pack-Monitor-{tag}")
    
    # 5. Backup DB
    db_path = os.path.join("recordings", "packing_records.db")
    if os.path.exists(db_path):
        shutil.copy2(db_path, db_path + ".bak")
    
    # 6. Copy with excludes
    excludes = {"recordings", "venv", "bin", "credentials.json", 
                ".env", "install_log.txt", "__pycache__"}
    for item in os.listdir(src_dir):
        if item in excludes:
            continue
        src = os.path.join(src_dir, item)
        dst = os.path.join(".", item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
    
    # 7. pip install
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                   timeout=120)
    
    # 8. npm build
    subprocess.run(["cmd", "/c", "npm run build"], cwd="web-ui", timeout=120)
    
    # 9. Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)
    
    # 10. Schedule restart
    _schedule_restart()
```

## Testing Checklist

- [ ] Dev mode: `git pull` update works
- [ ] Production mode: download ZIP + extract works
- [ ] DB backup trước update
- [ ] recordings/ không bị xóa
- [ ] venv/ không bị xóa
- [ ] bin/ không bị xóa
- [ ] Version badge hiển thị đúng
- [ ] Update modal progress states
- [ ] Server restart sau update
- [ ] Rollback nếu update fail (restore DB backup)

## Files Cần Tạo/Sửa

| File | Action |
|------|--------|
| `VERSION` | Tạo mới — chứa version string |
| `api.py` | Thêm 2 endpoints: `/api/system/update-check` + `/api/system/update` |
| `web-ui/src/App.jsx` | Version badge + update modal + progress |
| `.gitignore` | Thêm `*.db.bak` |

## Ghi Chú

- GitHub API có rate limit 60 requests/hour (unauthenticated). Đủ cho check mỗi startup.
- Nếu cần nhiều hơn → dùng GitHub token (env var `GITHUB_TOKEN`).
- Restart trên Windows cần batch script riêng (không thể restart Python từ trong Python).
- macOS restart dùng `os.execv` hoặc shell script tương tự.
- Changelog hiển thị từ GitHub Release body (Markdown rendered).
