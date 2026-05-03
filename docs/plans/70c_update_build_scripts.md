# Plan 70C: Update Build Scripts + Version Scripts

> **Status:** READY
> **Priority:** HIGH — Step 3C of restructuring
> **Scope:** 3 file updates (file-path references, NOT Python imports)
> **Estimated Effort:** 10 min

---

## Prerequisites

- Plan 70A (files moved) MUST be done
- Plan 70B (tests pass) MUST be done

---

## Goal

Fix 3 files that reference `api.py` by file path (not Python import). These will break silently if not updated.

---

## Step 1: Update `build.py` (CRITICAL — hard breakage)

**Current** (line 59):
```python
a = Analysis(["api.py"], ...)
```

**After**:
```python
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parent
# ... later:
a = Analysis([str(PROJECT_ROOT / "vpack" / "app.py")], ...)
```

**NOTE**: Current `build.py` does NOT have `--hidden-import` flags for project modules — only third-party packages (telebot, uvicorn, fastapi, etc.). After moving to `vpack/`, you may need to ADD hidden-import lines if PyInstaller can't auto-detect them. Test build first, add only if needed:
```python
# ADD these ONLY if PyInstaller fails to find vpack modules:
"--hidden-import=vpack",
"--hidden-import=vpack.app",
"--hidden-import=vpack.auth",
# ... etc.
```

Also fix relative path: `os.chdir("web-ui")` → `os.chdir(PROJECT_ROOT / "web-ui")`.

---

## Step 2: Update `scripts/bump_version.py` (silent failure)

**Current** (line 26):
```python
api_file = root_dir / "api.py"
```

**After**:
```python
api_file = root_dir / "vpack" / "app.py"
```

---

## Step 3: Update `scripts/check_version_consistency.py` (silent failure)

**Current** (line 21):
```python
api_file = root_dir / "api.py"
```

**After**:
```python
api_file = root_dir / "vpack" / "app.py"
```

---

## Verification

1. `ruff check build.py scripts/bump_version.py scripts/check_version_consistency.py` — no errors
2. `python scripts/check_version_consistency.py` — works, reports version consistency
3. `grep -rn "api.py" build.py scripts/bump_version.py scripts/check_version_consistency.py` — returns 0 results
4. `python build.py` — PyInstaller build succeeds (optional, takes time)
