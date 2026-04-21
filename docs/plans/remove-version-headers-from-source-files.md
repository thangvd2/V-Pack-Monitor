# Plan: Remove version headers from individual source files

**Ngay**: 2026-04-22
**Muc do**: Medium — Reduce version bump noise from 21 files to 3 files
**Loai**: Cleanup / Developer experience
**Blocker for release?**: No — can merge independently

---

## Problem

Mỗi lần bump version phải sửa **21 files** (14 .py + 7 .jsx) chỉ để đổi 1 con số version.

Issues:
1. **Diff noise**: 21-file diff cho mỗi version bump, khó review actual changes
2. **Git blame pollution**: Version bump commit overwrite real change history
3. **Consistency risk**: 21 nơi có thể miss (đã xảy ra với v3.3.0 — nhiều files jumped 3.2.0→3.3.1)
4. **Maintenance overhead**: `bump_version.py` phải scan 21 files, regex phức tạp

## Solution: Single source of truth

**Giữ version chỉ ở 3 nơi:**

| File | Purpose |
|------|---------|
| `VERSION` | Single source of truth (text file) |
| `api.py` header | Backend entry point identity, read by `_read_version()` |
| `web-ui/package.json` | npm version, bump via `npm version` |

**Frontend**: Đã đọc version từ API (`/api/system/update-check` → `updateInfo.current_version`). Không hardcode version trong JSX.

**Backend**: Các file .py khác (auth.py, database.py, recorder.py...) không cần version header. Version được identify qua VERSION file + git tag.

## Files to change

### Group 1: Remove version number from 13 .py file headers

**Giữ**: `api.py` (entry point)
**Remove version**: 13 files — thay `v3.3.1` bằng chỉ giữ copyright

| File | Current header | New header |
|------|---------------|------------|
| `auth.py` | `# V-Pack Monitor - CamDongHang v3.3.1` | `# V-Pack Monitor - CamDongHang` |
| `build.py` | `# V-Pack Monitor - CamDongHang v3.3.1` + copyright lines | `# V-Pack Monitor - CamDongHang` + copyright lines |
| `cloud_sync.py` | `# V-Pack Monitor - CamDongHang v3.3.1` | `# V-Pack Monitor - CamDongHang` |
| `database.py` | `# V-Pack Monitor - CamDongHang v3.3.1` | `# V-Pack Monitor - CamDongHang` |
| `network.py` | `# V-Pack Monitor - CamDongHang v3.3.1` + copyright lines | `# V-Pack Monitor - CamDongHang` + copyright lines |
| `recorder.py` | `# V-Pack Monitor - CamDongHang v3.3.1` | `# V-Pack Monitor - CamDongHang` |
| `routes_auth.py` | `# V-Pack Monitor - CamDongHang v3.3.1` + copyright lines | `# V-Pack Monitor - CamDongHang` + copyright lines |
| `routes_records.py` | `# V-Pack Monitor - CamDongHang v3.3.1` | `# V-Pack Monitor - CamDongHang` |
| `routes_stations.py` | `# V-Pack Monitor - CamDongHang v3.3.1` + copyright lines | `# V-Pack Monitor - CamDongHang` + copyright lines |
| `routes_system.py` | `# V-Pack Monitor - CamDongHang v3.3.1` | `# V-Pack Monitor - CamDongHang` |
| `telegram_bot.py` | `# V-Pack Monitor - CamDongHang v3.3.1` | `# V-Pack Monitor - CamDongHang` |
| `test_rtsp.py` | `# V-Pack Monitor - CamDongHang v3.3.1` + copyright lines | `# V-Pack Monitor - CamDongHang` + copyright lines |
| `video_worker.py` | `# V-Pack Monitor - CamDongHang v3.3.1` | `# V-Pack Monitor - CamDongHang` |

**Regex để tìm và replace:**
```python
# Remove version from Python headers (except api.py)
pattern = r"^((?:# )V-Pack Monitor(?: - CamDongHang)?\s+)v\d+\.\d+\.\d+"
replacement = r"\1"
# Apply to all .py files EXCEPT api.py
```

### Group 2: Remove version number from 6 .jsx file headers

**Remove version từ tất cả** — frontend đọc version từ API, không cần hardcode.

| File | Current header | New header |
|------|---------------|------------|
| `App.jsx` | `* V-Pack Monitor - CamDongHang v3.3.1` | `* V-Pack Monitor - CamDongHang` |
| `Dashboard.jsx` | same | same |
| `main.jsx` | same | same |
| `SetupModal.jsx` | same | same |
| `SystemHealth.jsx` | same | same |
| `UserManagementModal.jsx` | same | same |
| `VideoPlayerModal.jsx` | same | same |

**Note**: `App.jsx` đã có `updateInfo?.current_version` đọc từ API. Không cần hardcode.

**Regex:**
```python
# Remove version from JS/JSX headers
pattern = r"^((?: \* )V-Pack Monitor(?: - CamDongHang)?\s+)v\d+\.\d+\.\d+"
replacement = r"\1"
# Apply to all files in web-ui/src/
```

### Group 3: Simplify `bump_version.py`

**Xóa**: Logic scan 21 files (section "2. Update Python and Frontend headers")

**Giữ**: 
1. Update VERSION file
2. Update api.py header only
3. Update README.md
4. Update package.json

```python
# BEFORE: scan all .py + .jsx files
src_files = list(root_dir.glob("*.py")) + list((root_dir / "web-ui" / "src").rglob("*.[jt]s*"))
header_pattern = re.compile(...)
for src_file in src_files:
    # ...update each file

# AFTER: only update api.py
api_file = root_dir / "api.py"
if api_file.exists():
    content = api_file.read_text(encoding="utf-8")
    new_content, num = header_pattern.subn(rf"\g<1>{new_version}", content)
    if num > 0:
        api_file.write_text(new_content, encoding="utf-8")
        print("Updated api.py header")
```

### Group 4: Simplify `check_version_consistency.py`

**Xóa**: Logic scan 21 files

**Giữ**: Check VERSION == api.py header == package.json version == README.md version

```python
# BEFORE: scan all .py + .jsx files  
src_files = list(root_dir.glob("*.py")) + list((root_dir / "web-ui" / "src").rglob("*.[jt]s*"))
for src_file in src_files:
    # ...check each file

# AFTER: only check api.py
api_file = root_dir / "api.py"
if api_file.exists():
    content = api_file.read_text(encoding="utf-8")
    match = header_pattern.search(content)
    if match and match.group(1) != expected_version:
        errors.append(f"api.py: expected {expected_version}, found {match.group(1)}")
```

## Commit plan (4 commits)

| # | Commit message | Files |
|---|---------------|-------|
| 1 | `refactor: remove version from 13 Python file headers` | 13 .py files |
| 2 | `refactor: remove version from 7 Frontend file headers` | 7 .jsx files |
| 3 | `refactor: simplify bump_version.py to only touch api.py` | `scripts/bump_version.py` |
| 4 | `refactor: simplify check_version_consistency.py` | `scripts/check_version_consistency.py` |

## Test cases

1. **`python scripts/bump_version.py 9.9.9`** → Only changes VERSION, api.py, README.md, package.json — NOT auth.py, App.jsx, etc.
2. **`python scripts/check_version_consistency.py`** → Only checks VERSION == api.py == package.json == README — no longer scans 21 files
3. **`pytest tests/ -q`** passes
4. **`npm run build`** passes (frontend still builds without version in headers)
5. **Version displayed in UI** still works (reads from API `/api/system/update-check`)

## NOT changed

- `api.py` — keeps version header (entry point)
- `VERSION` file — single source of truth
- `README.md` — keeps version for public documentation
- `web-ui/package.json` — keeps version for npm
- Copyright lines — kept as-is, only version number removed
- `_read_version()` in api.py — already reads from VERSION file

## Impact analysis

| Metric | Before | After |
|--------|--------|-------|
| Files touched per version bump | 21 | 3 (+ README) |
| CI check files scanned | 21 | 1 (+ README + package.json) |
| Risk of version miss | 21 places | 3 places |
| Git diff lines per bump | ~42 lines | ~6 lines |
