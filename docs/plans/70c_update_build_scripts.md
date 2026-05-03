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

Fix 3 files that reference `api.py` by file path (not Python import). These will break silently if not updated — CI shows green even when broken.

---

## Step 1: Update `build.py` (CRITICAL — hard breakage)

**Current** (line 59):
```python
a = Analysis(["api.py"], ...)
```

**After**:
```python
PROJECT_ROOT = Path(__file__).resolve().parent
a = Analysis([str(PROJECT_ROOT / "vpack" / "app.py")], ...)
```

Also update ALL `--hidden-import` flags:
```python
# BEFORE:
"--hidden-import=auth",
"--hidden-import=database",
"--hidden-import=routes_auth",
# etc.

# AFTER:
"--hidden-import=vpack.auth",
"--hidden-import=vpack.database",
"--hidden-import=vpack.routes.auth",
"--hidden-import=vpack.routes.records",
"--hidden-import=vpack.routes.stations",
"--hidden-import=vpack.routes.system",
"--hidden-import=vpack.state",
"--hidden-import=vpack.cloud_sync",
"--hidden-import=vpack.network",
"--hidden-import=vpack.telegram_bot",
"--hidden-import=vpack.video_worker",
"--hidden-import=vpack.recorder",
```

**Read `build.py` fully** to find ALL hidden-import lines and update each one.

Also check for any other `api.py` string references in the file.

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
3. `grep -rn "api.py\|api:app" build.py scripts/bump_version.py scripts/check_version_consistency.py` — returns 0 results
4. `python build.py` — PyInstaller build succeeds (optional, takes time)

## After This Plan

Build and version tooling works with new `vpack/` layout. No silent failures. Plans 70A/B/C complete — all Python code in `vpack/`, all imports updated, all tools working.
