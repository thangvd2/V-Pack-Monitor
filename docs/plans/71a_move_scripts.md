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

**WARNING**: This is a STANDALONE installer (120 lines), NOT a wrapper for `install_macos.sh`. It has its own Python check, Node.js check, venv creation, pip install, npm build, MediaMTX download.

Changes needed:
1. **Fix cd** (line 7): `cd "$(dirname "$0")"` → `cd "$(dirname "$0")/.."` (MODIFY existing line, don't add new one)
2. **Add `pip install -e .`** after `pip install -r requirements.txt` (line 78)
3. **Update echoed instructions** (lines 115, 118-119): `./start.sh` → `./scripts/start.sh`

### 5. `Start V-Pack Monitor.command` → `scripts/Start V-Pack Monitor.command`

**MODIFY** existing cd (line 2): `cd "$(dirname "$0")"` → `cd "$(dirname "$0")/.."` (already has cd, just needs `..` appended)

Update uvicorn:
```bash
# BEFORE:
python3 -m uvicorn api:app

# AFTER:
python3 -m uvicorn vpack.app:app
```

### 6. `install_windows.bat` → `scripts/install_windows.bat`

**MODIFY** existing cd (line 3): `cd /d "%~dp0"` → `cd /d "%~dp0.."` (already has cd, just needs `..` appended)

Add `pip install -e .` after `pip install -r requirements.txt` (line 256).

### 7. `install_macos.sh` → `scripts/install_macos.sh`

Add at top:
```bash
cd "$(dirname "$0")/.."
```

Add `pip install -e .` after `pip install -r requirements.txt` (line 123).

**Update echoed instructions** (lines 167, 170-171): `./start.sh` → `./scripts/start.sh`

### 8. `inno_setup.iss` → `scripts/inno_setup.iss`

Exact fixes needed (all paths become relative to scripts/ instead of root):
- Line 9: `OutputDir=.\installer` → `OutputDir=..\installer`
- Line 17: `Source: "dist\V-Pack-Monitor.exe"` → `Source: "..\dist\V-Pack-Monitor.exe"`
- Line 19: `Source: "README.md"` → `Source: "..\README.md"`

---

## Verification

1. From project root: `scripts\start_windows.bat /?` or dry-run — cwd resolves to project root
2. `grep -rn "api:app" scripts/` — returns 0 results
3. `python scripts/build.py` — PyInstaller build works (if build.py hidden imports already updated in 70C)
4. No script files remain in root folder

## After This Plan

All scripts in `scripts/`. Root folder cleaner. Scripts work from new location.
