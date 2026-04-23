# Plan 51: Fix PyInstaller Hidden Imports

**Ngày**: 2026-04-24
**Mức độ**: High — EXE build crash khi import jwt, bcrypt, psutil
**Loại**: Bugfix

---

## Problem

`build.py` thiếu 3 hidden imports cho PyInstaller:
- `jwt` (PyJWT) — used in `auth.py` for JWT token creation/verification
- `bcrypt` — used in `auth.py` for password hashing
- `psutil` — used in `routes_system.py` for CPU/RAM/disk monitoring

Khi build EXE bằng `python build.py`, executable crash khi khởi động vì không tìm thấy module.

**Documented at**: `docs/windows_fixes_needed.md:36-64`

---

## Scope

### Files to change:
- `build.py` — Add 3 missing `--hidden-import` entries

### Current hidden imports (build.py:39-50):
```
telebot, uvicorn, fastapi, urllib3, boto3, google
```

### Missing:
```
jwt, bcrypt, psutil
```

### Fix:
```python
# Add after line 50:
"--hidden-import",
"jwt",
"--hidden-import",
"bcrypt",
"--hidden-import",
"psutil",
```

---

## Constraints

- Chỉ thêm hidden imports, không thay đổi logic build
- Giữ format `--hidden-import` + module name trên 2 dòng (matching existing style)
- Verify: `pyinstaller --help` confirms `--hidden-import` syntax

---

## Verification

- [ ] `python build.py` succeeds without errors
- [ ] Built executable starts without ImportError for jwt, bcrypt, psutil
- [ ] Login works (jwt + bcrypt)
- [ ] System Health tab loads (psutil)
- [ ] Existing hidden imports still work (telebot, uvicorn, etc.)
