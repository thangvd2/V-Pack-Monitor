> [!WARNING]
> **⚠️ OUTDATED — All issues fixed in v2.2.2 and v3.0.0. Kept for historical reference.**

# Windows Fixes Needed — V-Pack Monitor v2.1.0

> Các vấn đề cần fix khi chuyển sang làm việc trên máy Windows.

---

## 🔴 Issue #1: Camera Health Check — `ping -c` broken on Windows

**File:** `api.py` — dòng 1349-1350

**Vấn đề:** Endpoint `/api/system/network-info` dùng `ping -c 1 -W 1` (macOS/Linux). Trên Windows, flag này sai → camera luôn báo `reachable: false`.

**Code hiện tại (BROKEN on Windows):**
```python
result = subprocess.run(
    ["ping", "-c", "1", "-W", "1", ip], capture_output=True, timeout=2
)
```

**Fix — thay bằng platform check (giống pattern trong `network.py`):**
```python
import platform
system = platform.system()
if system == "Windows":
    result = subprocess.run(
        ["ping", "-n", "1", "-w", "1000", ip], capture_output=True, timeout=2
    )
else:
    result = subprocess.run(
        ["ping", "-c", "1", "-W", "1", ip], capture_output=True, timeout=2
    )
```

---

## 🟡 Issue #2: PyInstaller missing hidden imports

**File:** `build.py` — dòng 41-51

**Vấn đề:** `build.py` thiếu hidden imports cho các thư viện thêm từ v1.6→v2.1. PyInstaller `--onefile` sẽ không bundle được → exe crash on import.

**Code hiện tại — thiếu 3 thư viện:**
```python
    "--hidden-import",
    "boto3",
    "--hidden-import",
    "google",
    "--noconsole",
```

**Fix — thêm `jwt`, `bcrypt`, `psutil` trước `--noconsole`:**
```python
    "--hidden-import",
    "boto3",
    "--hidden-import",
    "google",
    "--hidden-import",
    "jwt",
    "--hidden-import",
    "bcrypt",
    "--hidden-import",
    "psutil",
    "--noconsole",
```

---

## ℹ️ Advisory: `psutil.disk_usage("/")` on Windows

**File:** `api.py` — dòng 1254

`psutil.disk_usage("/")` trả về ổ `C:\` trên Windows. Chấp nhận được nếu recordings nằm cùng ổ. Không cần fix trừ khi kho dùng ổ riêng cho recordings.
