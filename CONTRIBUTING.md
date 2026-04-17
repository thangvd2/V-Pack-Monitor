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

### Nguyên tắc cốt lõi: MERGE COMMIT, KHÔNG SQUASH

```
Feature PR → dev:   gh pr merge <N> --squash   ← 1 feature = 1 commit trên dev
Release PR → master: gh pr merge <N> --merge    ← giữ shared history, không conflict lần sau
```

**Tại sao phải --merge?** Squash merge tạo 1 commit mới trên master mà dev không share → phá vỡ shared history → mọi release sau đều conflict. Merge commit tạo 1 commit với 2 parents → git biết dev ≤ master → release sau clean.

### Quy trình chuẩn:

1. **Update version trên `dev`**:
   ```bash
   git checkout dev && git pull origin dev
   # Update VERSION file: v3.0.0 → v3.1.0
   # Update api.py header: v3.0.0 → v3.1.0
   # Add RELEASE_NOTES.md entry cho version mới
   git commit -m "release: vX.Y.Z — update VERSION, release notes"
   git push origin dev
   ```

2. **Tạo release branch từ `dev` và push**:
   ```bash
   git checkout -b release/vX.Y.Z dev
   git push origin release/vX.Y.Z
   ```

3. **Tạo PR: `release/vX.Y.Z` → `master`**:
   ```bash
   gh pr create --base master --title "Release vX.Y.Z" --body "..."
   ```

4. **Wait CI pass.** Nếu báo "not up to date with base" → merge master vào release branch:
   ```bash
   git fetch origin master
   git merge origin/master --no-edit
   git push origin release/vX.Y.Z
   # Wait CI pass again
   ```

5. **Merge bằng MERGE COMMIT (TUYỆT ĐỐI KHÔNG squash)**:
   ```bash
   gh pr merge <N> --merge    # ← QUAN TRỌNG: --merge, KHÔNG --squash
   ```

6. **Xong.** Dev và master share history. Release sau sẽ không conflict.

### Sole-Developer Merge Workaround

Sole developer với 1 GitHub account **không thể self-approve PR**. Khi branch protection yêu cầu reviews, dùng quy trình sau:

```bash
# 1. Tạm tắt required reviews
gh api repos/thangvd2/V-Pack-Monitor/branches/master/protection/required_pull_request_reviews \
  -X PATCH --input '{"required_approving_review_count": 0}'

# 2. Đợi GitHub propagate (ít nhất 30 giây)
sleep 30

# 3. Nếu vẫn BLOCKED → xóa protection tạm thời
gh api repos/thangvd2/V-Pack-Monitor/branches/master/protection -X DELETE
sleep 5

# 4. Merge
gh pr merge <N> --merge

# 5. Khôi phục protection ngay lập tức
gh api repos/thangvd2/V-Pack-Monitor/branches/master/protection -X PUT --input - <<'EOF'
{
  "required_status_checks": {
    "strict": false,
    "contexts": ["python-test", "frontend-build", "python-lint", "docs-only-bypass", "release-check"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": 0
  },
  "restrictions": null,
  "required_linear_history": false,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": false
}
EOF
```

**Lưu ý quan trọng**:
- `strict: false` — không yêu cầu CI chạy trên branch phải include master HEAD mới nhất. Tránh false-positive "not up to date" errors.
- GitHub API PATCH `required_reviews: 0` có propagation delay — có thể mất 30+ giây. Nếu gấp, DELETE protection + restore sau merge nhanh hơn.
- Luôn khôi phục protection **ngay sau khi merge** — không để branch unprotected.

### TUYỆT ĐỐI KHÔNG:
- ❌ `gh pr merge <N> --squash` cho release PR (dev → master) — phá vỡ shared history, gây conflict vĩnh viễn
- ❌ `git rebase` dev lên master — viết lại history, cùng vấn đề với squash
- ❌ `git cherry-pick` commits từ dev sang master — mất merge history
- ❌ `git push --force` master — mất release history
- ❌ Tạo release branch từ master rồi merge dev vào — ngược hướng, gây 12-file conflict

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
