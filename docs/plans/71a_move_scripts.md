# Plan 71A: Move Scripts to `scripts/` + CWD Fixes

> **Status:** READY
> **Priority:** HIGH — Step 4A of restructuring
> **Scope:** 8 scripts moved from root to `scripts/`
> **Estimated Effort:** 20 min

---

## Prerequisites

- Plans 68, 69A-C, 70A-C MUST be done
- All tests pass with modules in `vpack/`

---

## Goal

Move 8 root scripts into `scripts/` folder. Fix cwd resolution so scripts work from new location.

---

## Moves

### 1. `start_windows.bat` → `scripts/start_windows.bat`

Add at top of file (after `@echo off`):
```batch
cd /d "%~dp0.."
```
This sets cwd to project root regardless of where script is run from.

Update uvicorn:
```batch
REM BEFORE:
python -m uvicorn api:app --host 0.0.0.0 --port 8001

REM AFTER:
python -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001
```

### 2. `start.sh` → `scripts/start.sh`

Add at top of file (after shebang):
```bash
cd "$(dirname "$0")/.."
```

Update uvicorn:
```bash
# BEFORE:
python3 -m uvicorn api:app --host 0.0.0.0 --port 8001 &

# AFTER:
python3 -m uvicorn vpack.app:app --host 0.0.0.0 --port 8001 &
```

### 3. `build.py` → `scripts/build.py`

Add at top:
```python
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
```

Fix ALL relative paths:
- `os.chdir("web-ui")` → `os.chdir(PROJECT_ROOT / "web-ui")`
- `Analysis(["api.py"], ...)` → `Analysis([str(PROJECT_ROOT / "vpack" / "app.py")], ...)`
- Any other relative paths → use `PROJECT_ROOT / ...`

**Note**: PyInstaller hidden-import updates were already done in Plan 70C. Just verify they're correct.

### 4. `Install V-Pack Monitor.command` → `scripts/Install V-Pack Monitor.command`

Verify it calls `install_macos.sh` with correct path. If it uses relative path like `./install_macos.sh`, that will still work since both are now in `scripts/`.

May need `cd "$(dirname "$0")/.."` at top for other path resolution.

### 5. `Start V-Pack Monitor.command` → `scripts/Start V-Pack Monitor.command`

Add `cd "$(dirname "$0")/.."` if not present.

Update uvicorn:
```bash
# BEFORE:
python3 -m uvicorn api:app

# AFTER:
python3 -m uvicorn vpack.app:app
```

### 6. `install_windows.bat` → `scripts/install_windows.bat`

Add at top:
```batch
cd /d "%~dp0.."
```

Add `pip install -e .` after `pip install -r requirements.txt`.

Verify all `%CD%` paths still resolve correctly from project root.

### 7. `install_macos.sh` → `scripts/install_macos.sh`

Add at top:
```bash
cd "$(dirname "$0")/.."
```

Add `pip install -e .` after `pip install -r requirements.txt`.

### 8. `inno_setup.iss` → `scripts/inno_setup.iss`

Check for file paths inside the ISS file:
- `OutputDir=.\installer` — may need update if relative to ISS location
- Source executable path — update to `..\dist\...` or use absolute-ish path
- Icon path — same check

---

## Verification

1. From project root: `scripts\start_windows.bat /?` or dry-run — cwd resolves to project root
2. `grep -rn "api:app" scripts/` — returns 0 results
3. `python scripts/build.py` — PyInstaller build works (if build.py hidden imports already updated in 70C)
4. No script files remain in root folder

## After This Plan

All scripts in `scripts/`. Root folder cleaner. Scripts work from new location.
