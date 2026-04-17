# V-Pack Monitor — Quy trình Phát triển

## Branching

```
master          ← production-ready, LUÔN deployable
  └── dev       ← tích hợp tất cả feature
       ├── feature/xxx
       ├── fix/xxx
       └── security/xxx
```

### Quy tắc
- **Không push thẳng vào `master`** — mọi thay đổi qua Pull Request
- **`dev`** là branch tích hợp. Feature branch tách từ `dev`, merge ngược lại `dev`
- Khi `dev` ổn định → tạo PR `dev` → `master` → release
- Tên branch format: `feature/tên-mô-tả`, `fix/tên-mô-tả`, `security/tên-mô-tả`

## Pull Request

### Trước khi tạo PR
```bash
pip install -r requirements-dev.txt
pytest tests/ -v
cd web-ui && npm run build
```
Tất cả phải pass. CI sẽ kiểm tra lại nhưng cần pass locally trước.

### Checklist trong PR
Xem `.github/pull_request_template.md`. Yêu cầu bắt buộc:
- Không hardcode secret/credential
- Error path có logging, không silent `except: pass`
- File mới > 300 dòng → giải thích lý do trong PR description
- Mỗi commit chỉ nên chứa 1 loại thay đổi (formatting / feature / fix / docs). Không mix formatting với logic changes trong cùng commit

### Review
- Mỗi PR cần ít nhất 1 review trước khi merge
- AI review: chạy review workflow nếu thay đổi lớn
- File thay đổi > 200 dòng → review từng phần, không skim

## Versioning

Format: `vMAJOR.MINOR.PATCH`

| Loại | Khi nào | Ví dụ |
|------|---------|-------|
| PATCH | Bug fix, không thêm feature | v3.0.0 → v3.0.1 |
| MINOR | Feature mới, backward-compatible | v3.0.1 → v3.1.0 |
| MAJOR | Breaking change (API format, DB schema) | v3.1.0 → v4.0.0 |

Mỗi release phải có entry trong `RELEASE_NOTES.md`.

## Release Process (dev → master)

### Bước bắt buộc theo đúng thứ tự:

1. **Update version trên `dev`**:
   ```bash
   git checkout dev
   git pull origin dev
   # Update VERSION file: v3.0.0 → v3.1.0
   # Update api.py header: v3.0.0 → v3.1.0
   # Add RELEASE_NOTES.md entry cho version mới
   git commit -m "release: vX.Y.Z — update VERSION, release notes"
   git push origin dev
   ```

2. **Tạo release branch TỪ `dev` (KHÔNG phải master)**:
   ```bash
   git checkout -b release/vX.Y.Z dev
   ```

3. **Merge `master` vào release branch** (để git nhận ra shared history):
   ```bash
   git merge origin/master --no-ff
   ```

4. **Nếu conflict** — resolve bằng cách giữ **dev version** (dev luôn mới hơn):
   ```bash
   # List conflicts
   git diff --name-only --diff-filter=U
   # Resolve each — take dev version (ours)
   git diff --name-only --diff-filter=U | while IFS= read -r f; do
     git checkout --ours "$f" && git add "$f"
   done
   git commit -m "merge: resolve master..dev conflicts"
   ```

5. **Push và tạo PR**:
   ```bash
   git push -u origin release/vX.Y.Z
   gh pr create --base master --head release/vX.Y.Z --title "release: vX.Y.Z — ..."
   ```

6. **Verify CI pass** rồi merge PR.

### TUYỆT ĐỐI KHÔNG:
- ❌ Branch release từ `master` rồi merge dev vào — sẽ gây 12-file conflict do diverged history
- ❌ Cherry-pick commits từ dev sang master — mất merge history
- ❌ Force push master — mất release history
- ❌ Squash merge dev → master — mất individual commit history cho git blame

## CI Pipeline

Tự chạy trên mỗi push/PR nhắm vào `master` hoặc `dev`:

1. **Python Tests** — `pytest tests/` trên Python 3.13
2. **Frontend Build** — `npm ci && npm run build` trên Node 22
3. **Python Lint** — `ruff check` phát hiện code smell cơ bản

CI fail → **không merge**.

## Thay đổi quan trọng — Quy tắc đặc biệt

### Database migration
- Thay đổi schema → PHẢI có migration path (không drop column không có fallback)
- Luôn test với DB có data cũ

### Security
- Thay đổi auth/encryption → tạo PR riêng, mô tả chi tiết impact
- Không đổi HTTP status code đang dùng mà không ghi rõ trong PR

### Dependencies mới
- Thêm package → ghi lý do trong PR
- Kiểm tra license compatibility

## Cấu trúc dự án

```
├── api.py                  # FastAPI app, shared state, lifespan
├── routes_auth.py          # Auth + User management routes
├── routes_stations.py      # Station CRUD + sessions + discovery
├── routes_records.py       # Scan, records, download, SSE, live
├── routes_system.py        # Settings, analytics, health, update
├── database.py             # DB layer, encryption, FTS5
├── auth.py                 # JWT, password, token revocation
├── video_worker.py         # Video processing queue
├── recorder.py             # FFmpeg recording
├── cloud_sync.py           # Google Drive / S3 backup
├── telegram_bot.py         # Telegram notifications
├── network.py              # LAN scanner
├── tests/                  # Pytest test suite
├── web-ui/                 # React frontend
├── requirements.txt        # Python dependencies (production)
├── requirements-dev.txt    # Python dependencies (development only)
├── Dockerfile              # Docker deployment
├── install_windows.bat     # Windows installer
├── install_macos.sh        # macOS installer
├── start.sh                # macOS/Linux launcher
└── start_windows.bat       # Windows launcher
```
